<?php
namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\RegisterRequest;
use App\Http\Requests\Auth\LoginRequest;
use App\Http\Resources\UserResource;
use App\Models\User;
use App\Models\Role;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Hash;
use PHPOpenSourceSaver\JWTAuth\Facades\JWTAuth;

class AuthController extends Controller
{
    public function register(RegisterRequest $request): JsonResponse
    {
        $data = $request->validated();

        // admin role cannot be self-assigned
        if (($data['role'] ?? 'player') === 'admin') {
            return response()->json(['detail' => 'Cannot self-assign admin role.'], 403);
        }

        $user = User::create([
            'email'         => $data['email'],
            'username'      => $data['username'],
            'password_hash' => Hash::make($data['password']),
            'full_name'     => $data['full_name'],
            'role'          => $data['role'] ?? 'player',
        ]);

        // Assign role
        $roleName = $data['role'] ?? 'player';
        $role = Role::where('name', $roleName)->first();
        if ($role) {
            $user->roles()->attach($role->id, ['assigned_at' => now()]);
        }

        return response()->json(new UserResource($user->load('roles')), 201);
    }

    public function login(LoginRequest $request): JsonResponse
    {
        $data = $request->validated();

        $user = User::where('email', $data['email'])->first();

        if (!$user || !Hash::check($data['password'], $user->password_hash)) {
            return response()->json(['detail' => 'Invalid credentials.'], 401);
        }

        if (!$user->is_active) {
            return response()->json(['detail' => 'Account is locked.'], 403);
        }

        $user->update(['last_login_at' => now()]);
        $user->load('roles');

        $token = JWTAuth::fromUser($user);
        $ttl   = config('jwt.ttl', 60);

        return response()->json([
            'access_token' => $token,
            'token_type'   => 'bearer',
            'expires_in'   => $ttl * 60,
            'user'         => new UserResource($user),
        ]);
    }

    public function me(): JsonResponse
    {
        $user = JWTAuth::parseToken()->authenticate();
        return response()->json(new UserResource($user->load('roles')));
    }

    public function logout(): JsonResponse
    {
        JWTAuth::invalidate(JWTAuth::getToken());
        return response()->json(['detail' => 'Successfully logged out.']);
    }

    public function refresh(): JsonResponse
    {
        $newToken = JWTAuth::refresh(JWTAuth::getToken());
        return response()->json([
            'access_token' => $newToken,
            'token_type'   => 'bearer',
            'expires_in'   => config('jwt.ttl', 60) * 60,
        ]);
    }
}
