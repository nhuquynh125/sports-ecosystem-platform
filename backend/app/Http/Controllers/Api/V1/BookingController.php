<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\BookingResource;
use App\Models\Booking;
use App\Models\Court;
use App\Models\Venue;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class BookingController extends Controller
{
    // GET /bookings/mine - Current authenticated user bookings, paginated
    public function mine(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        $page = max(1, (int) $request->get('page', 1));
        $pageSize = min(100, max(1, (int) $request->get('page_size', 20)));

        $query = Booking::with(['court.venue', 'court.sport'])
            ->where('user_id', $user->id)
            ->orderBy('booking_date', 'desc')
            ->orderBy('time_slot', 'desc');

        $total = $query->count();
        $bookings = $query->skip(($page - 1) * $pageSize)->take($pageSize)->get();

        return response()->json([
            'items' => BookingResource::collection($bookings)->resolve(),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }

    // POST /bookings - Authenticated user creates booking
    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'court_id' => 'required|integer|exists:courts,id',
            'booking_date' => 'required|date_format:Y-m-d|after_or_equal:today',
            'time_slot' => 'required|date_format:H:i',
            'note' => 'nullable|string|max:255',
        ]);

        $user = auth('api')->user();
        $court = Court::findOrFail($data['court_id']);

        $normalizedTimeSlot = strlen($data['time_slot']) === 5 ? $data['time_slot'] . ':00' : $data['time_slot'];

        try {
            return DB::transaction(function () use ($data, $user, $court, $normalizedTimeSlot) {
                // Lock for update to prevent race conditions
                $existing = Booking::where('court_id', $data['court_id'])
                    ->where('booking_date', $data['booking_date'])
                    ->where('time_slot', $normalizedTimeSlot)
                    ->whereIn('status', ['confirmed', 'completed'])
                    ->lockForUpdate()
                    ->first();

                if ($existing) {
                    return response()->json(['detail' => 'This time slot is already booked.'], 409);
                }

                $bookingCode = 'BK-' . strtoupper(substr(md5(uniqid('', true)), 0, 8));
                $booking = Booking::create([
                    'booking_code' => $bookingCode,
                    'court_id' => $data['court_id'],
                    'user_id' => $user->id,
                    'booking_date' => $data['booking_date'],
                    'time_slot' => $normalizedTimeSlot,
                    'total_price' => $court->hourly_price,
                    'status' => 'confirmed',
                    'note' => $data['note'] ?? null,
                ]);

                $booking->load(['court.sport', 'court.venue']);
                return response()->json((new BookingResource($booking))->resolve(), 201);
            });
        } catch (\Illuminate\Database\QueryException $e) {
            if (str_contains($e->getMessage(), '23505') || str_contains($e->getMessage(), 'uq_bookings')) {
                return response()->json(['detail' => 'This time slot is already booked.'], 409);
            }
            throw $e;
        }
    }

    // DELETE /bookings/{id} - Cancel booking
    public function destroy(int $id, Request $request): JsonResponse
    {
        $user = auth('api')->user();
        $booking = Booking::with('court.venue')->findOrFail($id);

        $isOwner = $booking->court && $booking->court->venue && $booking->court->venue->owner_id === $user->id;
        $isBooker = $booking->user_id === $user->id;
        $isAdmin = $user->hasRole('admin');

        if (!$isBooker && !$isOwner && !$isAdmin) {
            abort(403, 'Unauthorized to cancel this booking');
        }

        if (in_array($booking->status, ['cancelled', 'completed'])) {
            return response()->json(['detail' => 'Booking cannot be cancelled in its current state.'], 400);
        }

        // Check if booking is in the past
        $dateStr = $booking->booking_date instanceof \DateTimeInterface
            ? $booking->booking_date->format('Y-m-d')
            : (string) $booking->booking_date;
        $slotStr = strlen($booking->time_slot) === 5 ? $booking->time_slot . ':00' : $booking->time_slot;
        $bookingStart = Carbon::parse($dateStr . ' ' . $slotStr);

        if ($bookingStart->isPast() && !$isAdmin) {
            return response()->json(['detail' => 'Past bookings cannot be cancelled.'], 400);
        }

        $booking->update([
            'status' => 'cancelled',
            'cancelled_at' => now(),
            'cancel_reason' => $request->input('cancel_reason', 'Cancelled by user'),
        ]);

        $booking->load(['court.sport', 'court.venue']);
        return response()->json((new BookingResource($booking))->resolve());
    }

    // GET /bookings/venue/{venueId} - Owner/Admin: list bookings for a venue, paginated
    public function venueBookings(int $venueId, Request $request): JsonResponse
    {
        $venue = Venue::findOrFail($venueId);
        $user = auth('api')->user();

        if ($venue->owner_id !== $user->id && !$user->hasRole('admin')) {
            abort(403, 'Not your venue');
        }

        $page = max(1, (int) $request->get('page', 1));
        $pageSize = min(100, max(1, (int) $request->get('page_size', 20)));

        $query = Booking::whereHas('court', fn($q) => $q->where('venue_id', $venueId))
            ->with(['court.sport', 'court.venue', 'user'])
            ->orderBy('booking_date', 'desc')
            ->orderBy('time_slot', 'desc');

        if ($request->filled('date')) {
            $query->where('booking_date', $request->date);
        }
        if ($request->filled('status')) {
            $query->where('status', $request->status);
        }

        $total = $query->count();
        $bookings = $query->skip(($page - 1) * $pageSize)->take($pageSize)->get();

        return response()->json([
            'items' => BookingResource::collection($bookings)->resolve(),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }
}
