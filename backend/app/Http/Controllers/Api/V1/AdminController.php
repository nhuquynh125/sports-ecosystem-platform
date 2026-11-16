<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\UserResource;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class AdminController extends Controller
{
    public function listUsers(Request $request): JsonResponse
    {
        $query = User::with('roles');

        if ($request->filled('q')) {
            $q = '%' . addcslashes($request->q, '%_') . '%';
            $query->where(function ($sub) use ($q) {
                $sub->where('full_name', 'ilike', $q)
                    ->orWhere('email', 'ilike', $q)
                    ->orWhere('username', 'ilike', $q);
            });
        }

        if ($request->filled('role')) {
            $query->whereHas('roles', function ($sub) use ($request) {
                $sub->where('name', $request->role);
            });
        }

        if ($request->has('is_active') && $request->is_active !== null && $request->is_active !== '') {
            $isActive = filter_var($request->is_active, FILTER_VALIDATE_BOOLEAN);
            $query->where('is_active', $isActive);
        }

        $page = max(1, (int) $request->input('page', 1));
        $pageSize = min(100, max(1, (int) $request->input('page_size', 20)));
        $total = $query->count();

        $users = $query->orderBy('id', 'desc')
            ->skip(($page - 1) * $pageSize)
            ->take($pageSize)
            ->get();

        return response()->json([
            'items' => UserResource::collection($users),
            'total' => $total,
            'page' => $page,
            'page_size' => $pageSize,
        ]);
    }

    public function getUser(int $id): JsonResponse
    {
        $user = User::with('roles')->findOrFail($id);
        return response()->json(new UserResource($user));
    }

    public function lockUser(int $id): JsonResponse
    {
        $user = User::with('roles')->findOrFail($id);
        $user->update(['is_active' => false]);
        return response()->json(new UserResource($user));
    }

    public function unlockUser(int $id): JsonResponse
    {
        $user = User::with('roles')->findOrFail($id);
        $user->update(['is_active' => true]);
        return response()->json(new UserResource($user));
    }

    public function updateUser(Request $request, int $id): JsonResponse
    {
        $user = User::with('roles')->findOrFail($id);

        $validated = $request->validate([
            'full_name' => 'nullable|string|max:150',
            'phone' => 'nullable|string|max:30',
            'avatar_url' => 'nullable|string|max:500',
            'date_of_birth' => 'nullable|date_format:Y-m-d',
            'is_active' => 'nullable|boolean',
            'allow_scouting' => 'nullable|boolean',
        ]);

        $user->update(array_filter($validated, fn($val) => $val !== null));
        $user->refresh()->load('roles');

        return response()->json(new UserResource($user));
    }
}
