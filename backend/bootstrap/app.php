<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Database\Eloquent\ModelNotFoundException;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Throwable;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->alias([
            'role' => \App\Http\Middleware\CheckRole::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
        );

        $exceptions->render(function (ValidationException $e, Request $request) {
            $formatted = [];
            foreach ($e->errors() as $field => $messages) {
                foreach ($messages as $msg) {
                    $formatted[] = "{$field}: {$msg}";
                }
            }
            return response()->json(['detail' => $formatted], 422);
        });

        $exceptions->render(function (AuthenticationException $e, Request $request) {
            return response()->json(['detail' => 'Unauthenticated'], 401);
        });

        $exceptions->render(function (AuthorizationException $e, Request $request) {
            return response()->json(['detail' => 'Forbidden'], 403);
        });

        $exceptions->render(function (ModelNotFoundException $e, Request $request) {
            return response()->json(['detail' => 'Resource not found'], 404);
        });

        $exceptions->render(function (HttpException $e, Request $request) {
            return response()->json(['detail' => $e->getMessage() ?: 'Error'], $e->getStatusCode());
        });

        $exceptions->render(function (Throwable $e, Request $request) {
            if (config('app.debug')) {
                return null;
            }
            return response()->json(['detail' => 'Internal server error'], 500);
        });
    })->create();
