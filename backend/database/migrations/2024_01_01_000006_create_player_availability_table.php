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
        Schema::create('player_availability', function (Blueprint $table) {
            $table->id();
            $table->foreignId('player_profile_id')->constrained('player_profiles')->onDelete('cascade');
            $table->smallInteger('day_of_week')->comment('0=Mon, 6=Sun');
            $table->time('start_time');
            $table->time('end_time');
            $table->timestampTz('created_at')->useCurrent();

            $table->index(['player_profile_id', 'day_of_week']);
        });

        DB::statement('ALTER TABLE player_availability ADD CONSTRAINT chk_availability_time CHECK (end_time > start_time)');
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('player_availability');
    }
};
