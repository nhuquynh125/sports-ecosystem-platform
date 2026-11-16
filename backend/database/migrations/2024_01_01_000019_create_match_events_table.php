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
        Schema::create('match_events', function (Blueprint $table) {
            $table->id();
            $table->foreignId('match_id')->constrained('tournament_matches')->onDelete('cascade');
            $table->foreignId('player_id')->nullable()->constrained('users')->onDelete('set null');
            $table->foreignId('team_id')->constrained('teams')->onDelete('cascade');
            $table->string('event_type', 20);
            $table->smallInteger('minute')->nullable();
            $table->string('notes', 255)->nullable();
            $table->timestampTz('created_at')->useCurrent();

            $table->index('match_id');
            $table->index('player_id');
            $table->index('team_id');
        });

        DB::statement("ALTER TABLE match_events ADD CONSTRAINT chk_match_events_event_type CHECK (event_type IN ('goal', 'assist', 'yellow_card', 'red_card', 'own_goal'))");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('match_events');
    }
};
