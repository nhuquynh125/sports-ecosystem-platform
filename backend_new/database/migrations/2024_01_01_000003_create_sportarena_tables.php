<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration {
    public function up(): void {
        Schema::create('teams', function (Blueprint $table) {
            $table->id();
            $table->string('name', 100);
            $table->string('slug', 110)->unique();
            $table->unsignedSmallInteger('sport_id');
            $table->unsignedBigInteger('captain_id');
            $table->text('description')->nullable();
            $table->string('logo_url', 500)->nullable();
            $table->string('city', 100)->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->foreign('captain_id')->references('id')->on('users')->onDelete('restrict');
        });

        Schema::create('team_members', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('team_id');
            $table->unsignedBigInteger('user_id');
            $table->string('role', 20)->default('member');
            $table->timestamps();
            $table->unique(['team_id', 'user_id']);
            $table->foreign('team_id')->references('id')->on('teams')->onDelete('cascade');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });
        DB::statement("ALTER TABLE team_members ADD CONSTRAINT ck_team_members_role CHECK (role IN ('captain','member'))");

        Schema::create('tournaments', function (Blueprint $table) {
            $table->id();
            $table->string('name', 150);
            $table->string('slug', 160)->unique();
            $table->unsignedSmallInteger('sport_id');
            $table->unsignedBigInteger('organizer_id');
            $table->string('format', 30)->default('round_robin');
            $table->string('status', 30)->default('draft');
            $table->text('description')->nullable();
            $table->string('city', 100)->nullable();
            $table->integer('max_teams')->nullable();
            $table->integer('min_teams')->default(2);
            $table->date('registration_deadline')->nullable();
            $table->date('start_date')->nullable();
            $table->date('end_date')->nullable();
            $table->decimal('entry_fee', 10, 2)->default(0);
            $table->string('prize_description', 500)->nullable();
            $table->timestamps();
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->foreign('organizer_id')->references('id')->on('users')->onDelete('restrict');
        });
        DB::statement("ALTER TABLE tournaments ADD CONSTRAINT ck_tournaments_format CHECK (format IN ('round_robin','single_elimination','double_elimination','group_stage'))");
        DB::statement("ALTER TABLE tournaments ADD CONSTRAINT ck_tournaments_status CHECK (status IN ('draft','open','registration_closed','ongoing','completed','cancelled'))");

        Schema::create('tournament_teams', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('tournament_id');
            $table->unsignedBigInteger('team_id');
            $table->string('status', 20)->default('pending');
            $table->unsignedBigInteger('approved_by')->nullable();
            $table->timestamp('approved_at')->nullable();
            $table->timestamps();
            $table->unique(['tournament_id', 'team_id']);
            $table->foreign('tournament_id')->references('id')->on('tournaments')->onDelete('cascade');
            $table->foreign('team_id')->references('id')->on('teams')->onDelete('restrict');
            $table->foreign('approved_by')->references('id')->on('users')->onDelete('set null');
        });
        DB::statement("ALTER TABLE tournament_teams ADD CONSTRAINT ck_tournament_teams_status CHECK (status IN ('pending','approved','rejected'))");

        Schema::create('tournament_groups', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('tournament_id');
            $table->string('name', 50);
            $table->timestamps();
            $table->foreign('tournament_id')->references('id')->on('tournaments')->onDelete('cascade');
        });

        Schema::create('group_teams', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('group_id');
            $table->unsignedBigInteger('team_id');
            $table->unique(['group_id', 'team_id']);
            $table->foreign('group_id')->references('id')->on('tournament_groups')->onDelete('cascade');
            $table->foreign('team_id')->references('id')->on('teams')->onDelete('restrict');
        });

        // Update chat_rooms to allow team_id and tournament_id FK (teams/tournaments now exist)
        Schema::table('chat_rooms', function (Blueprint $table) {
            $table->foreign('team_id')->references('id')->on('teams')->onDelete('cascade');
            $table->foreign('tournament_id')->references('id')->on('tournaments')->onDelete('cascade');
        });
    }

    public function down(): void {
        Schema::table('chat_rooms', function (Blueprint $table) {
            $table->dropForeign(['team_id']);
            $table->dropForeign(['tournament_id']);
        });
        Schema::dropIfExists('group_teams');
        Schema::dropIfExists('tournament_groups');
        Schema::dropIfExists('tournament_teams');
        Schema::dropIfExists('tournaments');
        Schema::dropIfExists('team_members');
        Schema::dropIfExists('teams');
    }
};
