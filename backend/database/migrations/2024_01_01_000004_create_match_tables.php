<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration {
    public function up(): void {
        Schema::create('tournament_matches', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('tournament_id');
            $table->unsignedBigInteger('group_id')->nullable();
            $table->unsignedBigInteger('home_team_id');
            $table->unsignedBigInteger('away_team_id');
            $table->unsignedBigInteger('court_id')->nullable();
            $table->date('match_date')->nullable();
            $table->time('time_slot')->nullable();
            $table->integer('home_score')->nullable();
            $table->integer('away_score')->nullable();
            $table->string('status', 20)->default('scheduled');
            $table->timestamps();
            $table->foreign('tournament_id')->references('id')->on('tournaments')->onDelete('cascade');
            $table->foreign('group_id')->references('id')->on('tournament_groups')->onDelete('set null');
            $table->foreign('home_team_id')->references('id')->on('teams')->onDelete('restrict');
            $table->foreign('away_team_id')->references('id')->on('teams')->onDelete('restrict');
            $table->foreign('court_id')->references('id')->on('courts')->onDelete('set null');
        });
        DB::statement("ALTER TABLE tournament_matches ADD CONSTRAINT ck_tournament_matches_status CHECK (status IN ('scheduled','ongoing','completed','cancelled','postponed'))");
        DB::statement("CREATE INDEX ix_tournament_matches_tournament_id ON tournament_matches (tournament_id)");
        DB::statement("CREATE INDEX ix_tournament_matches_match_date ON tournament_matches (match_date)");
        // No two matches can share court+date+slot
        DB::statement("CREATE UNIQUE INDEX uq_tournament_matches_court_date_slot ON tournament_matches (court_id, match_date, time_slot) WHERE court_id IS NOT NULL AND match_date IS NOT NULL AND time_slot IS NOT NULL");

        Schema::create('match_events', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('match_id');
            $table->unsignedBigInteger('player_id')->nullable();
            $table->unsignedBigInteger('team_id');
            $table->string('event_type', 20);
            $table->unsignedSmallInteger('minute')->nullable();
            $table->string('notes', 255)->nullable();
            $table->timestamp('created_at')->useCurrent();
            $table->foreign('match_id')->references('id')->on('tournament_matches')->onDelete('cascade');
            $table->foreign('player_id')->references('id')->on('users')->onDelete('set null');
            $table->foreign('team_id')->references('id')->on('teams')->onDelete('restrict');
        });
        DB::statement("ALTER TABLE match_events ADD CONSTRAINT ck_match_events_type CHECK (event_type IN ('goal','assist','yellow_card','red_card','own_goal'))");
    }

    public function down(): void {
        Schema::dropIfExists('match_events');
        Schema::dropIfExists('tournament_matches');
    }
};
