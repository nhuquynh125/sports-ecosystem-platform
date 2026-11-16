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
        Schema::create('tournament_matches', function (Blueprint $table) {
            $table->id();
            $table->foreignId('tournament_id')->constrained('tournaments')->onDelete('cascade');
            $table->foreignId('group_id')->nullable()->constrained('tournament_groups')->onDelete('set null');
            $table->foreignId('home_team_id')->constrained('teams')->onDelete('restrict');
            $table->foreignId('away_team_id')->constrained('teams')->onDelete('restrict');
            $table->foreignId('court_id')->nullable()->constrained('courts')->onDelete('set null');
            $table->date('match_date')->nullable();
            $table->time('time_slot')->nullable();
            $table->integer('home_score')->nullable();
            $table->integer('away_score')->nullable();
            $table->string('status', 20)->default('scheduled');
            $table->timestamps();

            $table->index('tournament_id');
            $table->index('group_id');
            $table->index('match_date');
            $table->index('status');
        });

        DB::statement("ALTER TABLE tournament_matches ADD CONSTRAINT chk_tournament_matches_status CHECK (status IN ('scheduled', 'ongoing', 'completed', 'cancelled', 'postponed'))");
        DB::statement("CREATE UNIQUE INDEX uq_tournament_matches_court_slot ON tournament_matches (court_id, match_date, time_slot) WHERE court_id IS NOT NULL AND match_date IS NOT NULL AND time_slot IS NOT NULL");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('tournament_matches');
    }
};
