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
        Schema::create('teams', function (Blueprint $table) {
            $table->id();
            $table->string('name', 100);
            $table->string('slug', 110)->unique();
            $table->unsignedSmallInteger('sport_id');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
            $table->foreignId('captain_id')->constrained('users')->onDelete('restrict');
            $table->text('description')->nullable();
            $table->string('logo_url', 500)->nullable();
            $table->string('city', 100)->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();

            $table->index('sport_id');
            $table->index('captain_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('teams');
    }
};
