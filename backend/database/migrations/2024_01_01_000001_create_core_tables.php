<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration {
    public function up(): void {
        // Enable PostgreSQL extensions
        DB::statement('CREATE EXTENSION IF NOT EXISTS citext');
        DB::statement('CREATE EXTENSION IF NOT EXISTS btree_gist');

        // roles
        Schema::create('roles', function (Blueprint $table) {
            $table->smallIncrements('id');
            $table->string('name', 30)->unique();
            $table->string('description', 255)->nullable();
        });

        DB::table('roles')->insert([
            ['name' => 'admin',       'description' => 'Operates the platform: users, roles, approvals, catalogue'],
            ['name' => 'player',      'description' => 'Books courts, keeps a profile, joins teams and matches'],
            ['name' => 'venue_owner', 'description' => 'Owns venues and courts, manages bookings'],
            ['name' => 'organizer',   'description' => 'Creates tournaments and reviews registrations'],
            ['name' => 'coach',       'description' => 'Uses statistics and AI scouting, manages watchlists'],
        ]);

        // users (use citext via raw column type for email/username on pgsql, fallback string)
        Schema::create('users', function (Blueprint $table) {
            $table->id();
            $table->string('email', 254)->unique();
            $table->string('username', 50)->unique();
            $table->string('password_hash', 255);
            $table->string('full_name', 150);
            $table->string('phone', 30)->nullable();
            $table->string('avatar_url', 500)->nullable();
            $table->date('date_of_birth')->nullable();
            $table->boolean('is_active')->default(true);
            $table->boolean('allow_scouting')->default(false);
            $table->timestamp('last_login_at')->nullable();
            $table->timestamps();
        });

        // user_roles pivot
        Schema::create('user_roles', function (Blueprint $table) {
            $table->unsignedBigInteger('user_id');
            $table->unsignedSmallInteger('role_id');
            $table->timestamp('assigned_at')->useCurrent();
            $table->unsignedBigInteger('assigned_by')->nullable();
            $table->primary(['user_id', 'role_id']);
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
            $table->foreign('role_id')->references('id')->on('roles')->onDelete('restrict');
            $table->foreign('assigned_by')->references('id')->on('users')->onDelete('set null');
        });

        // sports
        Schema::create('sports', function (Blueprint $table) {
            $table->smallIncrements('id');
            $table->string('name', 60)->unique();
            $table->string('slug', 70)->unique();
            $table->string('icon_url', 500)->nullable();
            $table->string('description', 500)->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        // player_profiles
        Schema::create('player_profiles', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id')->unique();
            $table->unsignedSmallInteger('sport_id');
            $table->string('skill_level', 20)->default('beginner');
            $table->string('position', 50)->nullable();
            $table->string('city', 100)->nullable();
            $table->string('bio', 500)->nullable();
            $table->boolean('is_visible')->default(true);
            $table->timestamps();
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
        });
        DB::statement("ALTER TABLE player_profiles ADD CONSTRAINT ck_player_profiles_skill_level CHECK (skill_level IN ('beginner','intermediate','advanced','pro'))");

        // player_availability
        Schema::create('player_availability', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('player_profile_id');
            $table->unsignedTinyInteger('day_of_week'); // 1=Mon, 7=Sun
            $table->time('start_time');
            $table->time('end_time');
            $table->timestamps();
            $table->foreign('player_profile_id')->references('id')->on('player_profiles')->onDelete('cascade');
        });
        DB::statement("ALTER TABLE player_availability ADD CONSTRAINT ck_player_availability_dow CHECK (day_of_week BETWEEN 1 AND 7)");
        DB::statement("ALTER TABLE player_availability ADD CONSTRAINT ck_player_availability_time CHECK (end_time > start_time)");

        // notifications
        Schema::create('notifications', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id');
            $table->string('type', 50);
            $table->string('title', 150);
            $table->text('body')->nullable();
            $table->json('data')->nullable();
            $table->boolean('is_read')->default(false);
            $table->timestamp('read_at')->nullable();
            $table->timestamp('created_at')->useCurrent();
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });
        DB::statement("CREATE INDEX ix_notifications_user_unread ON notifications (user_id, is_read, created_at DESC)");

        // chat_rooms
        Schema::create('chat_rooms', function (Blueprint $table) {
            $table->id();
            $table->string('type', 20);
            $table->string('name', 150)->nullable();
            $table->unsignedBigInteger('team_id')->nullable()->unique();
            $table->unsignedBigInteger('tournament_id')->nullable()->unique();
            $table->unsignedBigInteger('created_by')->nullable();
            $table->timestamp('created_at')->useCurrent();
            $table->foreign('created_by')->references('id')->on('users')->onDelete('set null');
        });
        DB::statement("ALTER TABLE chat_rooms ADD CONSTRAINT ck_chat_rooms_type CHECK (type IN ('direct','team','tournament'))");

        // chat_room_members
        Schema::create('chat_room_members', function (Blueprint $table) {
            $table->unsignedBigInteger('room_id');
            $table->unsignedBigInteger('user_id');
            $table->timestamp('joined_at')->useCurrent();
            $table->timestamp('last_read_at')->nullable();
            $table->primary(['room_id', 'user_id']);
            $table->foreign('room_id')->references('id')->on('chat_rooms')->onDelete('cascade');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('cascade');
        });

        // chat_messages
        Schema::create('chat_messages', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('room_id');
            $table->unsignedBigInteger('sender_id')->nullable();
            $table->text('content');
            $table->string('message_type', 20)->default('text');
            $table->timestamp('created_at')->useCurrent();
            $table->timestamp('edited_at')->nullable();
            $table->timestamp('deleted_at')->nullable();
            $table->foreign('room_id')->references('id')->on('chat_rooms')->onDelete('cascade');
            $table->foreign('sender_id')->references('id')->on('users')->onDelete('set null');
        });
        DB::statement("ALTER TABLE chat_messages ADD CONSTRAINT ck_chat_messages_type CHECK (message_type IN ('text','image','system'))");
        DB::statement("CREATE INDEX ix_chat_messages_room_created ON chat_messages (room_id, created_at DESC)");
    }

    public function down(): void {
        Schema::dropIfExists('chat_messages');
        Schema::dropIfExists('chat_room_members');
        Schema::dropIfExists('chat_rooms');
        Schema::dropIfExists('notifications');
        Schema::dropIfExists('player_availability');
        Schema::dropIfExists('player_profiles');
        Schema::dropIfExists('sports');
        Schema::dropIfExists('user_roles');
        Schema::dropIfExists('users');
        Schema::dropIfExists('roles');
    }
};
