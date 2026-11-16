<?php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpKernel\Exception\HttpException;

class CheckRole
{
    public function handle(Request $request, Closure $next, string ...$roles): mixed
    {
        $user = auth('api')->user();
        if (!$user) {
            throw new HttpException(401, 'Unauthenticated');
        }
        foreach ($roles as $role) {
            if ($user->hasRole($role)) {
                return $next($request);
            }
        }
        throw new HttpException(403, 'Insufficient permissions');
    }
}
