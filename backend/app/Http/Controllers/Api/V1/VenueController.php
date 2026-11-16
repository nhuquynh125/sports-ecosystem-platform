<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\CourtResource;
use App\Http\Resources\VenueDetailResource;
use App\Http\Resources\VenueListResource;
use App\Http\Resources\OwnerVenueResource;
use App\Models\Booking;
use App\Models\Court;
use App\Models\Venue;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class VenueController extends Controller
{
    // GET /venues - Public. Query params: sport_id, city, q, page, page_size
    public function index(Request $request): JsonResponse
    {
        $query = Venue::where('is_active', true)
            ->with(['courts' => fn($q) => $q->where('is_active', true)->with('sport')]);

        if ($request->filled('sport_id')) {
            $query->whereHas('courts', fn($q) => $q->where('sport_id', $request->sport_id)->where('is_active', true));
        }
        if ($request->filled('city')) {
            $query->whereRaw('LOWER(city) = ?', [strtolower($request->city)]);
        }
        if ($request->filled('q')) {
            $term = '%' . addcslashes($request->q, '%_') . '%';
            $query->where(fn($qb) => $qb->where('name', 'ilike', $term)
                ->orWhere('description', 'ilike', $term)
                ->orWhere('address', 'ilike', $term));
        }

        $page = max(1, (int) $request->get('page', 1));
        $pageSize = min(100, max(1, (int) $request->get('page_size', 20)));
        $total = $query->count();
        $venues = $query->orderBy('name')->skip(($page - 1) * $pageSize)->take($pageSize)->get();

        return response()->json([
            'items' => VenueListResource::collection($venues)->resolve(),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }

    // GET /venues/{id} - Public
    public function show(int $venueId): JsonResponse
    {
        $venue = Venue::with(['courts' => fn($q) => $q->where('is_active', true)->with('sport')])
            ->findOrFail($venueId);

        if (!$venue->is_active) {
            abort(404, 'Venue not found');
        }

        return response()->json((new VenueDetailResource($venue))->resolve());
    }

    // GET /venues/{id}/availability?date=YYYY-MM-DD - Public
    public function availability(int $venueId, Request $request): JsonResponse
    {
        $request->validate(['date' => 'required|date_format:Y-m-d']);
        $venue = Venue::with(['courts' => fn($q) => $q->where('is_active', true)->with('sport')])->findOrFail($venueId);
        if (!$venue->is_active) {
            abort(404, 'Venue not found');
        }

        $date = $request->date;
        $today = now()->toDateString();
        $nowTime = now()->format('H:i:s');

        // Normalize open_time and close_time to H:i:s
        $openTimeStr = strlen($venue->open_time) === 5 ? $venue->open_time . ':00' : $venue->open_time;
        $closeTimeStr = strlen($venue->close_time) === 5 ? $venue->close_time . ':00' : $venue->close_time;

        // Get all bookings for this venue/date in one query
        $bookedSet = Booking::whereHas('court', fn($q) => $q->where('venue_id', $venueId))
            ->where('booking_date', $date)
            ->whereIn('status', ['confirmed', 'completed'])
            ->get(['court_id', 'time_slot'])
            ->mapWithKeys(function ($b) {
                $slot = strlen($b->time_slot) === 5 ? $b->time_slot . ':00' : $b->time_slot;
                return [$b->court_id . '_' . $slot => true];
            })
            ->toArray();

        // Generate 1-hour slots from open_time to close_time
        $slots = $this->generateSlots($openTimeStr, $closeTimeStr);

        $courts = $venue->courts->map(function (Court $court) use ($bookedSet, $slots, $date, $today, $nowTime) {
            $courtSlots = collect($slots)->map(function ($startTime) use ($court, $bookedSet, $date, $today, $nowTime) {
                $key = $court->id . '_' . $startTime;
                $endTime = Carbon::createFromFormat('H:i:s', $startTime)->addHour()->format('H:i:s');
                if (isset($bookedSet[$key])) {
                    $status = 'booked';
                } elseif ($date < $today || ($date === $today && $startTime <= $nowTime)) {
                    $status = 'past';
                } else {
                    $status = 'available';
                }
                return [
                    'start_time' => $startTime,
                    'end_time' => $endTime,
                    'status' => $status,
                    'price' => (float) $court->hourly_price,
                ];
            });

            return [
                'court' => (new CourtResource($court))->resolve(),
                'slots' => $courtSlots->toArray(),
            ];
        });

        return response()->json([
            'venue_id' => $venueId,
            'date' => $date,
            'slot_minutes' => 60,
            'open_time' => $venue->open_time,
            'close_time' => $venue->close_time,
            'courts' => $courts->toArray(),
        ]);
    }

    private function generateSlots(string $openTime, string $closeTime): array
    {
        $slots = [];
        $current = Carbon::createFromFormat('H:i:s', $openTime);
        $close = Carbon::createFromFormat('H:i:s', $closeTime)->subHour();
        while ($current->lte($close)) {
            $slots[] = $current->format('H:i:s');
            $current->addHour();
        }
        return $slots;
    }

    // GET /venues/owner/mine - Owner/Admin
    public function myVenues(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        $page = max(1, (int) $request->get('page', 1));
        $pageSize = min(100, max(1, (int) $request->get('page_size', 20)));
        $query = Venue::with(['courts.sport'])->where('owner_id', $user->id);
        $total = $query->count();
        $venues = $query->orderBy('name')->skip(($page - 1) * $pageSize)->take($pageSize)->get();

        return response()->json([
            'items' => OwnerVenueResource::collection($venues)->resolve(),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }

    // POST /venues - Owner/Admin
    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'name' => 'required|string|max:150',
            'description' => 'nullable|string',
            'address' => 'required|string|max:255',
            'city' => 'required|string|max:100',
            'district' => 'nullable|string|max:100',
            'phone' => 'nullable|string|max:30',
            'open_time' => 'required|date_format:H:i',
            'close_time' => 'required|date_format:H:i|after:open_time',
            'is_active' => 'boolean',
        ]);

        $venue = Venue::create(array_merge($data, ['owner_id' => auth('api')->id()]));
        $venue->load('courts.sport');

        return response()->json((new OwnerVenueResource($venue))->resolve(), 201);
    }

    // PATCH /venues/{id} - Owner/Admin
    public function update(int $venueId, Request $request): JsonResponse
    {
        $venue = Venue::findOrFail($venueId);
        $user = auth('api')->user();
        if ($venue->owner_id !== $user->id && !$user->hasRole('admin')) {
            abort(403, 'Not your venue');
        }

        $data = $request->validate([
            'name' => 'sometimes|string|max:150',
            'description' => 'nullable|string',
            'address' => 'sometimes|string|max:255',
            'city' => 'sometimes|string|max:100',
            'district' => 'nullable|string|max:100',
            'phone' => 'nullable|string|max:30',
            'open_time' => 'sometimes|date_format:H:i',
            'close_time' => 'sometimes|date_format:H:i',
            'is_active' => 'boolean',
        ]);

        $venue->update($data);
        $venue->load('courts.sport');

        return response()->json((new OwnerVenueResource($venue))->resolve());
    }

    // DELETE /venues/{id} - Owner/Admin
    public function destroy(int $venueId): JsonResponse
    {
        $venue = Venue::findOrFail($venueId);
        $user = auth('api')->user();
        if ($venue->owner_id !== $user->id && !$user->hasRole('admin')) {
            abort(403, 'Not your venue');
        }

        $venue->delete();
        return response()->json(null, 204);
    }

    // POST /venues/{id}/courts - Owner/Admin
    public function createCourt(int $venueId, Request $request): JsonResponse
    {
        $venue = Venue::findOrFail($venueId);
        $user = auth('api')->user();
        if ($venue->owner_id !== $user->id && !$user->hasRole('admin')) {
            abort(403, 'Not your venue');
        }

        $data = $request->validate([
            'sport_id' => 'required|integer|exists:sports,id',
            'name' => 'required|string|max:100',
            'surface_type' => 'nullable|in:grass,turf,wood,hard,clay,synthetic',
            'capacity' => 'nullable|integer|min:1',
            'hourly_price' => 'required|numeric|min:0',
            'is_active' => 'boolean',
        ]);

        $court = Court::create(array_merge($data, ['venue_id' => $venueId]));
        $court->load('sport');

        return response()->json((new CourtResource($court))->resolve(), 201);
    }

    // PATCH /venues/{id}/courts/{courtId} - Owner/Admin
    public function updateCourt(int $venueId, int $courtId, Request $request): JsonResponse
    {
        $court = Court::where('venue_id', $venueId)->findOrFail($courtId);
        $venue = Venue::findOrFail($venueId);
        $user = auth('api')->user();
        if ($venue->owner_id !== $user->id && !$user->hasRole('admin')) {
            abort(403, 'Not your venue');
        }

        $data = $request->validate([
            'name' => 'sometimes|string|max:100',
            'surface_type' => 'nullable|in:grass,turf,wood,hard,clay,synthetic',
            'capacity' => 'nullable|integer|min:1',
            'hourly_price' => 'sometimes|numeric|min:0',
            'is_active' => 'boolean',
        ]);

        $court->update($data);
        $court->load('sport');

        return response()->json((new CourtResource($court))->resolve());
    }

    // DELETE /venues/{id}/courts/{courtId}
    public function destroyCourt(int $venueId, int $courtId): JsonResponse
    {
        $court = Court::where('venue_id', $venueId)->findOrFail($courtId);
        $venue = Venue::findOrFail($venueId);
        $user = auth('api')->user();
        if ($venue->owner_id !== $user->id && !$user->hasRole('admin')) {
            abort(403, 'Not your venue');
        }

        $court->delete();
        return response()->json(null, 204);
    }
}
