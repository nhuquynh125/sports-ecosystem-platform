<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\UserResource;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function me(): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }
        $user->load('roles');
        return response()->json(new UserResource($user));
    }

    public function updateMe(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $validated = $request->validate([
            'full_name' => 'nullable|string|max:150',
            'phone' => 'nullable|string|max:30',
            'avatar_url' => 'nullable|string|max:500',
            'date_of_birth' => 'nullable|date_format:Y-m-d',
            'allow_scouting' => 'nullable|boolean',
        ]);

        $user->update(array_filter($validated, fn($val) => $val !== null));
        $user->load('roles');

        return response()->json(new UserResource($user));
    }

    public function changePassword(Request $request): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }

        $request->validate([
            'current_password' => 'required|string',
            'new_password' => 'required|string|min:8',
        ]);

        if (!Hash::check($request->current_password, $user->password_hash)) {
            return response()->json(['detail' => 'Current password does not match'], 400);
        }

        $user->update([
            'password_hash' => Hash::make($request->new_password),
        ]);

        return response()->json(['detail' => 'Password updated successfully']);
    }
}
