<?php

use Illuminate\Support\Facades\Route;

// Health check
Route::get('/health', fn() => response()->json(['status' => 'ok', 'service' => 'sports-ecosystem-api', 'version' => '1.0.0']));

// Auth routes (no prefix needed — bootstrap adds api/v1)
Route::prefix('auth')->group(function () {
    Route::post('/register', [\App\Http\Controllers\Auth\AuthController::class, 'register']);
    Route::post('/login',    [\App\Http\Controllers\Auth\AuthController::class, 'login']);
    Route::get('/me',        [\App\Http\Controllers\Auth\AuthController::class, 'me'])->middleware('auth.jwt');
    Route::post('/logout',   [\App\Http\Controllers\Auth\AuthController::class, 'logout'])->middleware('auth.jwt');
    Route::post('/refresh',  [\App\Http\Controllers\Auth\AuthController::class, 'refresh'])->middleware('auth.jwt');
});

// Protected routes
Route::middleware('auth.jwt')->group(function () {
    // Users / Profile
    Route::get('/users',    [\App\Http\Controllers\UserController::class, 'index'])->middleware('role:admin');
    Route::get('/users/{id}', [\App\Http\Controllers\UserController::class, 'show']);
    Route::patch('/users/me', [\App\Http\Controllers\UserController::class, 'updateMe']);
    Route::patch('/users/me/password', [\App\Http\Controllers\UserController::class, 'changePassword']);

    // Admin user management
    Route::prefix('admin')->middleware('role:admin')->group(function () {
        Route::patch('/users/{id}/status', [\App\Http\Controllers\Admin\AdminUserController::class, 'updateStatus']);
        Route::patch('/users/{id}/roles',  [\App\Http\Controllers\Admin\AdminUserController::class, 'updateRoles']);
    });

    // Sports
    Route::get('/sports', [\App\Http\Controllers\SportController::class, 'index']);
    Route::post('/sports', [\App\Http\Controllers\SportController::class, 'store'])->middleware('role:admin');
    Route::get('/sports/{id}', [\App\Http\Controllers\SportController::class, 'show']);
    Route::put('/sports/{id}', [\App\Http\Controllers\SportController::class, 'update'])->middleware('role:admin');
    Route::delete('/sports/{id}', [\App\Http\Controllers\SportController::class, 'destroy'])->middleware('role:admin');

    // Player profiles
    Route::get('/players/profile', [\App\Http\Controllers\PlayerProfileController::class, 'myProfile']);
    Route::post('/players/profile', [\App\Http\Controllers\PlayerProfileController::class, 'store']);
    Route::put('/players/profile', [\App\Http\Controllers\PlayerProfileController::class, 'update']);
    Route::get('/players/{userId}/profile', [\App\Http\Controllers\PlayerProfileController::class, 'show']);
    Route::get('/players/profile/availability', [\App\Http\Controllers\PlayerProfileController::class, 'availability']);
    Route::post('/players/profile/availability', [\App\Http\Controllers\PlayerProfileController::class, 'addAvailability']);
    Route::delete('/players/profile/availability/{id}', [\App\Http\Controllers\PlayerProfileController::class, 'removeAvailability']);

    // Notifications
    Route::get('/notifications', [\App\Http\Controllers\NotificationController::class, 'index']);
    Route::patch('/notifications/{id}/read', [\App\Http\Controllers\NotificationController::class, 'markRead']);
    Route::patch('/notifications/read-all', [\App\Http\Controllers\NotificationController::class, 'readAll']);

    // Chat
    Route::get('/chat/rooms', [\App\Http\Controllers\ChatController::class, 'rooms']);
    Route::post('/chat/rooms', [\App\Http\Controllers\ChatController::class, 'createRoom']);
    Route::get('/chat/rooms/{roomId}/messages', [\App\Http\Controllers\ChatController::class, 'messages']);
    Route::post('/chat/rooms/{roomId}/messages', [\App\Http\Controllers\ChatController::class, 'sendMessage']);

    // Venues & Courts (CourtBook Module)
    Route::get('/venues', [\App\Http\Controllers\VenueController::class, 'index']);
    Route::post('/venues', [\App\Http\Controllers\VenueController::class, 'store'])->middleware('role:venue_owner,admin');
    Route::get('/venues/{id}', [\App\Http\Controllers\VenueController::class, 'show']);
    Route::put('/venues/{id}', [\App\Http\Controllers\VenueController::class, 'update'])->middleware('role:venue_owner,admin');
    Route::delete('/venues/{id}', [\App\Http\Controllers\VenueController::class, 'destroy'])->middleware('role:venue_owner,admin');
    Route::get('/venues/{id}/availability', [\App\Http\Controllers\VenueController::class, 'availability']);
    Route::get('/venues/{id}/courts', [\App\Http\Controllers\CourtController::class, 'byVenue']);
    Route::post('/venues/{id}/courts', [\App\Http\Controllers\CourtController::class, 'store'])->middleware('role:venue_owner,admin');

    // Bookings
    Route::get('/bookings', [\App\Http\Controllers\BookingController::class, 'index']);
    Route::post('/bookings', [\App\Http\Controllers\BookingController::class, 'store']);
    Route::get('/bookings/{id}', [\App\Http\Controllers\BookingController::class, 'show']);
    Route::delete('/bookings/{id}', [\App\Http\Controllers\BookingController::class, 'destroy']);

    // Teams (SportArena)
    Route::get('/teams', [\App\Http\Controllers\TeamController::class, 'index']);
    Route::post('/teams', [\App\Http\Controllers\TeamController::class, 'store']);
    Route::get('/teams/{id}', [\App\Http\Controllers\TeamController::class, 'show']);
    Route::put('/teams/{id}', [\App\Http\Controllers\TeamController::class, 'update']);
    Route::delete('/teams/{id}', [\App\Http\Controllers\TeamController::class, 'destroy']);
    Route::post('/teams/{id}/members', [\App\Http\Controllers\TeamController::class, 'addMember']);
    Route::delete('/teams/{id}/members/{userId}', [\App\Http\Controllers\TeamController::class, 'removeMember']);

    // Tournaments
    Route::get('/tournaments', [\App\Http\Controllers\TournamentController::class, 'index']);
    Route::post('/tournaments', [\App\Http\Controllers\TournamentController::class, 'store'])->middleware('role:organizer,admin');
    Route::get('/tournaments/{id}', [\App\Http\Controllers\TournamentController::class, 'show']);
    Route::put('/tournaments/{id}', [\App\Http\Controllers\TournamentController::class, 'update'])->middleware('role:organizer,admin');
    Route::delete('/tournaments/{id}', [\App\Http\Controllers\TournamentController::class, 'destroy'])->middleware('role:organizer,admin');
    Route::post('/tournaments/{id}/register', [\App\Http\Controllers\TournamentController::class, 'registerTeam']);
    Route::patch('/tournaments/{id}/teams/{teamId}/approve', [\App\Http\Controllers\TournamentController::class, 'approveTeam'])->middleware('role:organizer,admin');
    Route::patch('/tournaments/{id}/teams/{teamId}/reject', [\App\Http\Controllers\TournamentController::class, 'rejectTeam'])->middleware('role:organizer,admin');
    Route::post('/tournaments/{id}/groups', [\App\Http\Controllers\TournamentController::class, 'assignGroups'])->middleware('role:organizer,admin');
    Route::post('/tournaments/{id}/generate-schedule', [\App\Http\Controllers\TournamentController::class, 'generateSchedule'])->middleware('role:organizer,admin');
    Route::get('/tournaments/{id}/matches', [\App\Http\Controllers\TournamentController::class, 'matches']);
    Route::patch('/tournaments/{id}/matches/{matchId}/result', [\App\Http\Controllers\TournamentController::class, 'updateMatchResult'])->middleware('role:organizer,admin');
    Route::get('/tournaments/{id}/standings', [\App\Http\Controllers\TournamentController::class, 'standings']);
    Route::get('/tournaments/{id}/top-scorers', [\App\Http\Controllers\TournamentController::class, 'topScorers']);

    // Pickup Matches (SportHub)
    Route::get('/matches', [\App\Http\Controllers\PickupMatchController::class, 'index']);
    Route::post('/matches', [\App\Http\Controllers\PickupMatchController::class, 'store']);
    Route::get('/matches/{id}', [\App\Http\Controllers\PickupMatchController::class, 'show']);
    Route::put('/matches/{id}', [\App\Http\Controllers\PickupMatchController::class, 'update']);
    Route::delete('/matches/{id}', [\App\Http\Controllers\PickupMatchController::class, 'destroy']);
    Route::post('/matches/{id}/join', [\App\Http\Controllers\PickupMatchController::class, 'join']);
    Route::delete('/matches/{id}/leave', [\App\Http\Controllers\PickupMatchController::class, 'leave']);
    Route::post('/matches/{id}/ratings', [\App\Http\Controllers\PickupMatchController::class, 'rate']);

    // AI Smart Match
    Route::post('/ai/smart-match', [\App\Http\Controllers\AI\SmartMatchController::class, 'recommend']);
});
