<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('group_teams', function (Blueprint $table) {
            $table->id();
            $table->foreignId('group_id')->constrained('tournament_groups')->onDelete('cascade');
            $table->foreignId('tournament_id')->constrained('tournaments')->onDelete('cascade');
            $table->foreignId('tournament_team_id')->constrained('tournament_teams')->onDelete('cascade');
            $table->integer('seeding')->nullable();

            $table->unique(['group_id', 'tournament_team_id']);
            $table->unique(['tournament_id', 'tournament_team_id']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('group_teams');
    }
};
