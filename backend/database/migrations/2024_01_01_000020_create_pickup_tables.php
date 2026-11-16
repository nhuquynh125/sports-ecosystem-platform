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
        // 1. pickup_matches
        Schema::create('pickup_matches', function (Blueprint $table) {
            $table->id();
            $table->foreignId('host_id')->constrained('users')->onDelete('restrict');
            $table->unsignedSmallInteger('sport_id');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->string('title', 150);
            $table->text('description')->nullable();
            $table->string('area', 100);
            $table->foreignId('venue_id')->nullable()->constrained('venues')->onDelete('set null');
            $table->foreignId('court_id')->nullable()->constrained('courts')->onDelete('set null');
            $table->date('match_date');
            $table->time('time_slot');
            $table->smallInteger('duration_minutes')->default(60);
            $table->smallInteger('max_players');
            $table->string('skill_level', 20)->default('intermediate');
            $table->string('status', 20)->default('open');
            $table->foreignId('chat_room_id')->nullable()->constrained('chat_rooms')->onDelete('set null');
            $table->timestamps();

            $table->index('host_id');
            $table->index('sport_id');
            $table->index('match_date');
            $table->index('status');
            $table->index('area');
        });

        DB::statement("ALTER TABLE pickup_matches ADD CONSTRAINT chk_pickup_matches_skill_level CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'pro'))");
        DB::statement("ALTER TABLE pickup_matches ADD CONSTRAINT chk_pickup_matches_status CHECK (status IN ('open', 'full', 'completed', 'cancelled'))");

        // 2. match_players
        Schema::create('match_players', function (Blueprint $table) {
            $table->id();
            $table->foreignId('match_id')->constrained('pickup_matches')->onDelete('cascade');
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->string('status', 20)->default('joined');
            $table->boolean('attended')->default(false);
            $table->timestampTz('joined_at')->useCurrent();

            $table->unique(['match_id', 'user_id']);
            $table->index('match_id');
            $table->index('user_id');
        });

        DB::statement("ALTER TABLE match_players ADD CONSTRAINT chk_match_players_status CHECK (status IN ('joined', 'left', 'no_show'))");

        // 3. pickup_ratings
        Schema::create('pickup_ratings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('match_id')->constrained('pickup_matches')->onDelete('cascade');
            $table->foreignId('rater_id')->constrained('users')->onDelete('cascade');
            $table->foreignId('rated_user_id')->constrained('users')->onDelete('cascade');
            $table->smallInteger('skill_score');
            $table->smallInteger('punctuality_score');
            $table->text('comment')->nullable();
            $table->timestampTz('created_at')->useCurrent();

            $table->unique(['match_id', 'rater_id', 'rated_user_id']);
        });

        DB::statement("ALTER TABLE pickup_ratings ADD CONSTRAINT chk_pickup_ratings_skill_score CHECK (skill_score BETWEEN 1 AND 5)");
        DB::statement("ALTER TABLE pickup_ratings ADD CONSTRAINT chk_pickup_ratings_punctuality_score CHECK (punctuality_score BETWEEN 1 AND 5)");
        DB::statement("ALTER TABLE pickup_ratings ADD CONSTRAINT chk_pickup_ratings_not_self CHECK (rater_id <> rated_user_id)");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('pickup_ratings');
        Schema::dropIfExists('match_players');
        Schema::dropIfExists('pickup_matches');
    }
};
