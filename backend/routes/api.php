<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\V1\AuthController;
use App\Http\Controllers\Api\V1\UserController;
use App\Http\Controllers\Api\V1\SportController;
use App\Http\Controllers\Api\V1\PlayerProfileController;
use App\Http\Controllers\Api\V1\NotificationController;
use App\Http\Controllers\Api\V1\ChatController;
use App\Http\Controllers\Api\V1\AdminController;
use App\Http\Controllers\Api\V1\VenueController;
use App\Http\Controllers\Api\V1\BookingController;

Route::prefix('v1')->group(function () {
    // Health check
    Route::get('/health', fn() => response()->json(['status' => 'ok', 'service' => 'sports-ecosystem-api']));

    // Auth routes
    Route::prefix('auth')->group(function () {
        Route::post('/register', [AuthController::class, 'register'])->name('auth.register');
        Route::post('/login', [AuthController::class, 'login'])->name('auth.login');
        Route::get('/me', [AuthController::class, 'me'])->middleware('auth:api')->name('auth.me');
    });

    // Sports (public GET)
    Route::get('/sports', [SportController::class, 'index']);
    Route::get('/sports/{id}', [SportController::class, 'show']);

    // Player profiles (public GET)
    Route::get('/player-profiles', [PlayerProfileController::class, 'index']);
    Route::get('/player-profiles/{id}', [PlayerProfileController::class, 'show']);
    Route::get('/player-profiles/{profileId}/availability', [PlayerProfileController::class, 'listAvailability']);

    // Venues (public routes)
    Route::get('/venues', [VenueController::class, 'index']);
    Route::get('/venues/{id}/availability', [VenueController::class, 'availability']);
    Route::get('/venues/{id}', [VenueController::class, 'show']);

    // Authenticated routes
    Route::middleware('auth:api')->group(function () {
        // User routes
        Route::get('/users/me', [UserController::class, 'me']);
        Route::patch('/users/me', [UserController::class, 'updateMe']);
        Route::post('/users/me/change-password', [UserController::class, 'changePassword']);

        // Sports (admin POST/PATCH)
        Route::post('/sports', [SportController::class, 'store'])->middleware('role:admin');
        Route::patch('/sports/{id}', [SportController::class, 'update'])->middleware('role:admin');

        // Player profiles
        Route::get('/player-profiles/mine', [PlayerProfileController::class, 'mine']);
        Route::post('/player-profiles', [PlayerProfileController::class, 'store'])->middleware('role:player,coach');
        Route::patch('/player-profiles/{id}', [PlayerProfileController::class, 'update'])->middleware('role:player,coach');
        Route::delete('/player-profiles/{id}', [PlayerProfileController::class, 'destroy'])->middleware('role:player,coach');

        // Player availability
        Route::post('/player-profiles/{profileId}/availability', [PlayerProfileController::class, 'addAvailability']);
        Route::delete('/player-profiles/{profileId}/availability/{slotId}', [PlayerProfileController::class, 'deleteAvailability']);

        // Notifications
        Route::get('/notifications', [NotificationController::class, 'index']);
        Route::patch('/notifications/read-all', [NotificationController::class, 'readAll']);
        Route::patch('/notifications/{id}/read', [NotificationController::class, 'read']);

        // Chat
        Route::get('/chat/rooms', [ChatController::class, 'listRooms']);
        Route::post('/chat/rooms', [ChatController::class, 'createRoom']);
        Route::get('/chat/rooms/{roomId}/messages', [ChatController::class, 'listMessages']);
        Route::post('/chat/rooms/{roomId}/messages', [ChatController::class, 'sendMessage']);

        // Admin
        Route::prefix('admin')->middleware('role:admin')->group(function () {
            Route::get('/users', [AdminController::class, 'listUsers']);
            Route::get('/users/{id}', [AdminController::class, 'getUser']);
            Route::patch('/users/{id}', [AdminController::class, 'updateUser']);
            Route::post('/users/{id}/lock', [AdminController::class, 'lockUser']);
            Route::post('/users/{id}/unlock', [AdminController::class, 'unlockUser']);
        });

        // Venues - authenticated routes (must put owner/mine before {id} to avoid collision)
        Route::get('/venues/owner/mine', [VenueController::class, 'myVenues'])->middleware('role:venue_owner,admin');
        Route::post('/venues', [VenueController::class, 'store'])->middleware('role:venue_owner,admin');
        Route::patch('/venues/{id}', [VenueController::class, 'update'])->middleware('role:venue_owner,admin');
        Route::delete('/venues/{id}', [VenueController::class, 'destroy'])->middleware('role:venue_owner,admin');
        Route::post('/venues/{id}/courts', [VenueController::class, 'createCourt'])->middleware('role:venue_owner,admin');
        Route::patch('/venues/{id}/courts/{courtId}', [VenueController::class, 'updateCourt'])->middleware('role:venue_owner,admin');
        Route::delete('/venues/{id}/courts/{courtId}', [VenueController::class, 'destroyCourt'])->middleware('role:venue_owner,admin');

        // Bookings
        Route::get('/bookings/mine', [BookingController::class, 'mine']);
        Route::post('/bookings', [BookingController::class, 'store']);
        Route::delete('/bookings/{id}', [BookingController::class, 'destroy']);
        Route::get('/bookings/venue/{venueId}', [BookingController::class, 'venueBookings'])->middleware('role:venue_owner,admin');
    });
});
