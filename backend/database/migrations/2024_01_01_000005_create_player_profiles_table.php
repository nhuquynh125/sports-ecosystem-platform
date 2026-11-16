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
        Schema::create('player_profiles', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->unsignedSmallInteger('sport_id');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->string('position', 50)->nullable();
            $table->string('skill_level', 20)->default('intermediate');
            $table->string('preferred_side', 10)->nullable();
            $table->smallInteger('height_cm')->nullable();
            $table->decimal('weight_kg', 5, 2)->nullable();
            $table->string('city', 100)->nullable();
            $table->text('bio')->nullable();
            $table->boolean('is_visible')->default(true);
            $table->timestamps();

            $table->unique(['user_id', 'sport_id']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('player_profiles');
    }
};
