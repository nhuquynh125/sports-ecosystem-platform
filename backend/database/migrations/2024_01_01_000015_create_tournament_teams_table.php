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
        Schema::create('tournament_teams', function (Blueprint $table) {
            $table->id();
            $table->foreignId('tournament_id')->constrained('tournaments')->onDelete('cascade');
            $table->foreignId('team_id')->constrained('teams')->onDelete('cascade');
            $table->string('registration_status', 20)->default('pending');
            $table->foreignId('registered_by')->constrained('users')->onDelete('restrict');
            $table->foreignId('reviewed_by')->nullable()->constrained('users')->onDelete('set null');
            $table->timestampTz('reviewed_at')->nullable();
            $table->string('rejection_reason', 255)->nullable();
            $table->timestampTz('registered_at')->useCurrent();

            $table->unique(['tournament_id', 'team_id']);
            $table->index('tournament_id');
            $table->index('team_id');
            $table->index('registration_status');
        });

        DB::statement("ALTER TABLE tournament_teams ADD CONSTRAINT chk_tournament_teams_status CHECK (registration_status IN ('pending', 'approved', 'rejected'))");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('tournament_teams');
    }
};
