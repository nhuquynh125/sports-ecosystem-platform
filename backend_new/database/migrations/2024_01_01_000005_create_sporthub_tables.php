<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration {
    public function up(): void {
        Schema::create('pickup_matches', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('host_id');
            $table->unsignedSmallInteger('sport_id');
            $table->string('title', 150);
            $table->text('description')->nullable();
            $table->string('area', 100)->nullable();
            $table->string('location_detail', 255)->nullable();
            $table->decimal('latitude', 9, 6)->nullable();
            $table->decimal('longitude', 9, 6)->nullable();
            $table->date('match_date');
            $table->time('time_slot');
            $table->integer('duration_minutes')->default(90);
            $table->integer('max_players')->default(10);
            $table->string('skill_level', 20)->default('intermediate');
            $table->string('status', 20)->default('open');
            $table->unsignedBigInteger('chat_room_id')->nullable();
            $table->timestamps();
            $table->foreign('host_id')->references('id')->on('users')->onDelete('restrict');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->foreign('chat_room_id')->references('id')->on('chat_rooms')->onDelete('set null');
        });
        DB::statement("ALTER TABLE pickup_matches ADD CONSTRAINT ck_pickup_matches_skill CHECK (skill_level IN ('beginner','intermediate','advanced','pro'))");
        DB::statement("ALTER TABLE pickup_matches ADD CONSTRAINT ck_pickup_matches_status CHECK (status IN ('open','full','ongoing','completed','cancelled'))");
        DB::statement("ALTER TABLE pickup_matches ADD CONSTRAINT ck_pickup_matches_max CHECK (max_players >= 2)");
        DB::statement("CREATE INDEX ix_pickup_matches_host_id ON pickup_matches (host_id)");
        DB::statement("CREATE INDEX ix_pickup_matches_sport_id ON pickup_matches (sport_id)");
        DB::statement("CREATE INDEX ix_pickup_matches_match_date ON pickup_matches (match_date)");
        DB::statement("CREATE INDEX ix_pickup_matches_status ON pickup_matches (status)");

        Schema::create('match_players', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('match_id');
            $table->unsignedBigInteger('user_id');
            $table->string('status', 20)->default('joined');
            $table->boolean('attended')->default(false);
            $table->timestamp('joined_at')->useCurrent();
            $table->unique(['match_id', 'user_id']);
            $table->foreign('match_id')->references('id')->on('pickup_matches')->onDelete('cascade');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });
        DB::statement("ALTER TABLE match_players ADD CONSTRAINT ck_match_players_status CHECK (status IN ('joined','left','removed'))");

        Schema::create('pickup_ratings', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('match_id');
            $table->unsignedBigInteger('rater_id');
            $table->unsignedBigInteger('rated_user_id');
            $table->unsignedTinyInteger('skill_score');
            $table->unsignedTinyInteger('punctuality_score');
            $table->text('comment')->nullable();
            $table->timestamp('created_at')->useCurrent();
            $table->unique(['match_id', 'rater_id', 'rated_user_id']);
            $table->foreign('match_id')->references('id')->on('pickup_matches')->onDelete('cascade');
            $table->foreign('rater_id')->references('id')->on('users')->onDelete('cascade');
            $table->foreign('rated_user_id')->references('id')->on('users')->onDelete('cascade');
        });
        DB::statement("ALTER TABLE pickup_ratings ADD CONSTRAINT ck_pickup_ratings_skill CHECK (skill_score BETWEEN 1 AND 5)");
        DB::statement("ALTER TABLE pickup_ratings ADD CONSTRAINT ck_pickup_ratings_punctuality CHECK (punctuality_score BETWEEN 1 AND 5)");
        DB::statement("ALTER TABLE pickup_ratings ADD CONSTRAINT ck_pickup_ratings_no_self CHECK (rater_id != rated_user_id)");
        DB::statement("CREATE INDEX ix_pickup_ratings_match_id ON pickup_ratings (match_id)");
        DB::statement("CREATE INDEX ix_pickup_ratings_rated_user ON pickup_ratings (rated_user_id)");
    }

    public function down(): void {
        Schema::dropIfExists('pickup_ratings');
        Schema::dropIfExists('match_players');
        Schema::dropIfExists('pickup_matches');
    }
};
