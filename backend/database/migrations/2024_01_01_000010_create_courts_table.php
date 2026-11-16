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
        Schema::create('courts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('venue_id')->constrained('venues')->onDelete('restrict');
            $table->unsignedSmallInteger('sport_id');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->string('name', 100);
            $table->string('surface_type', 20)->nullable();
            $table->smallInteger('capacity')->nullable();
            $table->decimal('hourly_price', 12, 2);
            $table->boolean('is_active')->default(true);
            $table->timestamps();

            $table->unique(['venue_id', 'name']);
            $table->index('venue_id');
            $table->index('sport_id');
        });

        DB::statement("ALTER TABLE courts ADD CONSTRAINT chk_courts_surface_type CHECK (surface_type IS NULL OR surface_type IN ('grass', 'turf', 'wood', 'hard', 'clay', 'synthetic'))");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('courts');
    }
};
