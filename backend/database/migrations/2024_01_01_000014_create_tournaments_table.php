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
        Schema::create('tournaments', function (Blueprint $table) {
            $table->id();
            $table->foreignId('organizer_id')->constrained('users')->onDelete('restrict');
            $table->unsignedSmallInteger('sport_id');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->string('name', 150);
            $table->string('slug', 170)->unique();
            $table->text('description')->nullable();
            $table->string('format', 30);
            $table->string('status', 30)->default('draft');
            $table->smallInteger('max_teams')->nullable();
            $table->date('start_date')->nullable();
            $table->date('end_date')->nullable();
            $table->foreignId('venue_id')->nullable()->constrained('venues')->onDelete('set null');
            $table->text('prize_info')->nullable();
            $table->decimal('entry_fee', 12, 2)->nullable()->default(0);
            $table->timestamps();

            $table->index('organizer_id');
            $table->index('sport_id');
            $table->index('status');
        });

        DB::statement("ALTER TABLE tournaments ADD CONSTRAINT chk_tournaments_format CHECK (format IN ('round_robin', 'single_elimination', 'double_elimination', 'group_stage'))");
        DB::statement("ALTER TABLE tournaments ADD CONSTRAINT chk_tournaments_status CHECK (status IN ('draft', 'open', 'registration_closed', 'ongoing', 'completed', 'cancelled'))");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('tournaments');
    }
};
