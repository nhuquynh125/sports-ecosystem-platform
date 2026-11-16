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
        Schema::create('chat_rooms', function (Blueprint $table) {
            $table->id();
            $table->string('type', 20); // direct, team, tournament
            $table->string('name', 150)->nullable();
            $table->unsignedBigInteger('team_id')->nullable();
            $table->unsignedBigInteger('tournament_id')->nullable();
            $table->foreignId('created_by')->nullable()->constrained('users')->onDelete('set null');
            $table->timestampTz('created_at')->useCurrent();
        });

        DB::statement("ALTER TABLE chat_rooms ADD CONSTRAINT chk_chat_room_type CHECK (type IN ('direct', 'team', 'tournament'))");

        Schema::create('chat_room_members', function (Blueprint $table) {
            $table->foreignId('room_id')->constrained('chat_rooms')->onDelete('cascade');
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->timestampTz('joined_at')->useCurrent();
            $table->timestampTz('last_read_at')->nullable();

            $table->primary(['room_id', 'user_id']);
        });

        Schema::create('chat_messages', function (Blueprint $table) {
            $table->id();
            $table->foreignId('room_id')->constrained('chat_rooms')->onDelete('cascade');
            $table->foreignId('sender_id')->nullable()->constrained('users')->onDelete('set null');
            $table->text('content');
            $table->string('message_type', 20)->default('text');
            $table->timestampTz('created_at')->useCurrent();
            $table->timestampTz('edited_at')->nullable();
            $table->timestampTz('deleted_at')->nullable();
        });

        DB::statement("ALTER TABLE chat_messages ADD CONSTRAINT chk_chat_message_type CHECK (message_type IN ('text', 'image', 'system'))");
        DB::statement('CREATE INDEX idx_chat_messages_room_created_at ON chat_messages (room_id, created_at DESC)');
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('chat_messages');
        Schema::dropIfExists('chat_room_members');
        Schema::dropIfExists('chat_rooms');
    }
};
