<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\AvailabilityResource;
use App\Http\Resources\PlayerProfileResource;
use App\Models\PlayerAvailability;
use App\Models\PlayerProfile;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class PlayerProfileController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $query = PlayerProfile::with(['sport', 'user'])->where('is_visible', true);

        if ($request->filled('sport_id')) {
            $query->where('sport_id', $request->sport_id);
        }

        if ($request->filled('city')) {
            $query->whereRaw('LOWER(city) = ?', [strtolower($request->city)]);
        }

        if ($request->filled('skill_level')) {
            $query->where('skill_level', $request->skill_level);
        }

        if ($request->filled('q')) {
            $q = '%' . addcslashes($request->q, '%_') . '%';
            $query->where(function ($sub) use ($q) {
                $sub->where('bio', 'ilike', $q)
                    ->orWhere('position', 'ilike', $q)
                    ->orWhere('city', 'ilike', $q)
                    ->orWhereHas('user', function ($uq) use ($q) {
                        $uq->where('full_name', 'ilike', $q)
                            ->orWhere('username', 'ilike', $q);
                    });
            });
        }

        $page = max(1, (int) $request->input('page', 1));
        $pageSize = min(100, max(1, (int) $request->input('page_size', 20)));
        $total = $query->count();

        $profiles = $query->orderBy('id', 'desc')
            ->skip(($page - 1) * $pageSize)
            ->take($pageSize)
            ->get();

        return response()->json([
            'items' => PlayerProfileResource::collection($profiles),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }

    public function show(int $id): JsonResponse
    {
        $profile = PlayerProfile::with(['sport', 'user'])->findOrFail($id);
        return response()->json(new PlayerProfileResource($profile));
    }

    public function mine(): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $profiles = PlayerProfile::with(['sport', 'user'])
            ->where('user_id', $user->id)
            ->get();

        return response()->json(PlayerProfileResource::collection($profiles));
    }

    public function store(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $validated = $request->validate([
            'sport_id' => 'required|integer|exists:sports,id',
            'position' => 'nullable|string|max:50',
            'skill_level' => 'nullable|string|in:beginner,intermediate,advanced,pro',
            'preferred_side' => 'nullable|string|max:10',
            'height_cm' => 'nullable|integer|min:50|max:250',
            'weight_kg' => 'nullable|numeric|min:20|max:300',
            'city' => 'nullable|string|max:100',
            'bio' => 'nullable|string',
            'is_visible' => 'nullable|boolean',
        ]);

        $existing = PlayerProfile::where('user_id', $user->id)
            ->where('sport_id', $validated['sport_id'])
            ->first();

        if ($existing) {
            return response()->json(['detail' => 'Profile already exists for this sport'], 400);
        }

        $validated['user_id'] = $user->id;
        $profile = PlayerProfile::create($validated);
        $profile->load(['sport', 'user']);

        return response()->json(new PlayerProfileResource($profile), 201);
    }

    public function update(Request $request, int $id): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $profile = PlayerProfile::findOrFail($id);

        if ($profile->user_id !== $user->id && !$user->hasRole('admin')) {
            return response()->json(['detail' => 'Forbidden'], 403);
        }

        $validated = $request->validate([
            'position' => 'nullable|string|max:50',
            'skill_level' => 'nullable|string|in:beginner,intermediate,advanced,pro',
            'preferred_side' => 'nullable|string|max:10',
            'height_cm' => 'nullable|integer|min:50|max:250',
            'weight_kg' => 'nullable|numeric|min:20|max:300',
            'city' => 'nullable|string|max:100',
            'bio' => 'nullable|string',
            'is_visible' => 'nullable|boolean',
        ]);

        $profile->update(array_filter($validated, fn($val) => $val !== null));
        $profile->refresh()->load(['sport', 'user']);

        return response()->json(new PlayerProfileResource($profile));
    }

    public function destroy(int $id): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $profile = PlayerProfile::findOrFail($id);

        if ($profile->user_id !== $user->id && !$user->hasRole('admin')) {
            return response()->json(['detail' => 'Forbidden'], 403);
        }

        $profile->delete();

        return response()->json(['detail' => 'Player profile deleted successfully']);
    }

    // Availability Sub-resource
    public function listAvailability(int $profileId): JsonResponse
    {
        $profile = PlayerProfile::findOrFail($profileId);
        $availabilities = PlayerAvailability::where('player_profile_id', $profile->id)
            ->orderBy('day_of_week')
            ->orderBy('start_time')
            ->get();

        return response()->json(AvailabilityResource::collection($availabilities));
    }

    public function addAvailability(Request $request, int $profileId): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $profile = PlayerProfile::findOrFail($profileId);
        if ($profile->user_id !== $user->id && !$user->hasRole('admin')) {
            return response()->json(['detail' => 'Forbidden'], 403);
        }

        $validated = $request->validate([
            'day_of_week' => 'required|integer|min:0|max:6',
            'start_time' => 'required|date_format:H:i',
            'end_time' => 'required|date_format:H:i|after:start_time',
        ]);

        $validated['player_profile_id'] = $profile->id;
        $slot = PlayerAvailability::create($validated);

        return response()->json(new AvailabilityResource($slot), 201);
    }

    public function deleteAvailability(int $profileId, int $slotId): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $profile = PlayerProfile::findOrFail($profileId);
        if ($profile->user_id !== $user->id && !$user->hasRole('admin')) {
            return response()->json(['detail' => 'Forbidden'], 403);
        }

        $slot = PlayerAvailability::where('player_profile_id', $profile->id)->findOrFail($slotId);
        $slot->delete();

        return response()->json(['detail' => 'Availability slot deleted successfully']);
    }
}
