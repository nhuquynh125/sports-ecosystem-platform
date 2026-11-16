<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;
use Illuminate\Auth\AuthenticationException;
use PHPOpenSourceSaver\JWTAuth\Exceptions\TokenExpiredException;
use PHPOpenSourceSaver\JWTAuth\Exceptions\TokenInvalidException;
use PHPOpenSourceSaver\JWTAuth\Exceptions\JWTException;
use Symfony\Component\HttpKernel\Exception\HttpException;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
        apiPrefix: 'api/v1',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->alias([
            'auth.jwt' => \App\Http\Middleware\JwtAuthenticate::class,
            'role'     => \App\Http\Middleware\CheckRole::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        // Always return JSON for API routes
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
        );

        // Validation errors → 422 { "detail": "...", "errors": {...} }
        $exceptions->render(function (ValidationException $e, Request $request) {
            if ($request->is('api/*') || $request->expectsJson()) {
                $firstMsg = collect($e->errors())->flatten()->first() ?? 'Validation failed';
                return response()->json([
                    'detail' => $firstMsg,
                    'errors' => $e->errors(),
                ], 422);
            }
        });

        // Auth errors → 401 { "detail": "..." }
        $exceptions->render(function (AuthenticationException $e, Request $request) {
            if ($request->is('api/*') || $request->expectsJson()) {
                return response()->json(['detail' => 'Unauthenticated.'], 401);
            }
        });

        // JWT token errors
        $exceptions->render(function (TokenExpiredException $e, Request $request) {
            return response()->json(['detail' => 'Token has expired.'], 401);
        });
        $exceptions->render(function (TokenInvalidException $e, Request $request) {
            return response()->json(['detail' => 'Token is invalid.'], 401);
        });
        $exceptions->render(function (JWTException $e, Request $request) {
            return response()->json(['detail' => 'Token error: ' . $e->getMessage()], 401);
        });

        // Generic HTTP errors → { "detail": "..." }
        $exceptions->render(function (HttpException $e, Request $request) {
            if ($request->is('api/*') || $request->expectsJson()) {
                return response()->json(['detail' => $e->getMessage() ?: 'HTTP Error'], $e->getStatusCode());
            }
        });

        // Catch-all → 500
        $exceptions->render(function (\Throwable $e, Request $request) {
            if ($request->is('api/*') || $request->expectsJson()) {
                $status = method_exists($e, 'getStatusCode') ? $e->getStatusCode() : 500;
                $msg = config('app.debug') ? $e->getMessage() : 'Server Error';
                return response()->json(['detail' => $msg], $status);
            }
        });
    })->create();
