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
        Schema::create('team_members', function (Blueprint $table) {
            $table->id();
            $table->foreignId('team_id')->constrained('teams')->onDelete('cascade');
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->string('role', 20)->default('member');
            $table->timestampTz('joined_at')->useCurrent();

            $table->unique(['team_id', 'user_id']);
            $table->index('team_id');
            $table->index('user_id');
        });

        DB::statement("ALTER TABLE team_members ADD CONSTRAINT chk_team_members_role CHECK (role IN ('captain', 'member'))");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('team_members');
    }
};
