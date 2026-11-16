<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\LoginRequest;
use App\Http\Requests\Auth\RegisterRequest;
use App\Http\Resources\UserResource;
use App\Models\Role;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Hash;
use Tymon\JWTAuth\Facades\JWTAuth;

class AuthController extends Controller
{
    public function register(RegisterRequest $request): JsonResponse
    {
        $role = Role::where('name', $request->role)->firstOrFail();

        $user = User::create([
            'email' => strtolower($request->email),
            'username' => $request->username,
            'password_hash' => Hash::make($request->password),
            'full_name' => $request->full_name,
            'is_active' => true,
        ]);
        $user->roles()->attach($role->id, ['assigned_at' => now()]);
        $user->load('roles');

        return response()->json(new UserResource($user), 201);
    }

    public function login(LoginRequest $request): JsonResponse
    {
        $user = User::where('email', strtolower($request->email))->first();

        if (!$user || !Hash::check($request->password, $user->password_hash)) {
            return response()->json(['detail' => 'Invalid credentials'], 401);
        }
        if (!$user->is_active) {
            return response()->json(['detail' => 'Account is disabled'], 403);
        }

        $token = JWTAuth::fromUser($user);
        $user->update(['last_login_at' => now()]);
        $user->load('roles');

        return response()->json([
            'access_token' => $token,
            'token_type' => 'bearer',
            'expires_in' => (int) config('jwt.ttl', 15) * 60,
            'user' => new UserResource($user),
        ]);
    }

    public function me(): JsonResponse
    {
        $user = auth('api')->user();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        }
        $user->load('roles');
        return response()->json(new UserResource($user));
    }
}
