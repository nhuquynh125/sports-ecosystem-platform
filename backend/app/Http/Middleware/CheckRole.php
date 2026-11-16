<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use PHPOpenSourceSaver\JWTAuth\Facades\JWTAuth;

class CheckRole
{
    public function handle(Request $request, Closure $next, string ...$roles): mixed
    {
        $user = JWTAuth::parseToken()->authenticate();
        if (!$user) {
            return response()->json(['detail' => 'Unauthenticated.'], 401);
        }

        $userRoles = $user->roles->pluck('name')->toArray();
        foreach ($roles as $role) {
            if (in_array($role, $userRoles)) {
                return $next($request);
            }
        }

        return response()->json(['detail' => 'Forbidden: insufficient role.'], 403);
    }
}
