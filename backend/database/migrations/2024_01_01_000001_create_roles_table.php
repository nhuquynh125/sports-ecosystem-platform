<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        DB::statement('CREATE EXTENSION IF NOT EXISTS citext');

        Schema::create('roles', function (Blueprint $table) {
            $table->smallIncrements('id');
            $table->string('name', 30)->unique();
            $table->string('description', 255)->nullable();
        });

        // Seed roles in migration
        DB::table('roles')->insert([
            ['name' => 'admin', 'description' => 'Platform administrator with full permissions'],
            ['name' => 'player', 'description' => 'Sports player looking for matches and bookings'],
            ['name' => 'venue_owner', 'description' => 'Owner or manager of sports venues and courts'],
            ['name' => 'organizer', 'description' => 'Tournament and event organizer'],
            ['name' => 'coach', 'description' => 'Sports coach or instructor'],
        ]);
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('roles');
    }
};
