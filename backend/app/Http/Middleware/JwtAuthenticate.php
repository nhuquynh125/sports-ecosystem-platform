<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use PHPOpenSourceSaver\JWTAuth\Facades\JWTAuth;
use PHPOpenSourceSaver\JWTAuth\Exceptions\JWTException;
use PHPOpenSourceSaver\JWTAuth\Exceptions\TokenExpiredException;
use PHPOpenSourceSaver\JWTAuth\Exceptions\TokenInvalidException;

class JwtAuthenticate
{
    public function handle(Request $request, Closure $next): mixed
    {
        try {
            $user = JWTAuth::parseToken()->authenticate();
            if (!$user) {
                return response()->json(['detail' => 'User not found.'], 401);
            }
            if (!$user->is_active) {
                return response()->json(['detail' => 'Account is locked.'], 403);
            }
        } catch (TokenExpiredException $e) {
            return response()->json(['detail' => 'Token has expired.'], 401);
        } catch (TokenInvalidException $e) {
            return response()->json(['detail' => 'Token is invalid.'], 401);
        } catch (JWTException $e) {
            return response()->json(['detail' => 'Token not provided.'], 401);
        }

        return $next($request);
    }
}
