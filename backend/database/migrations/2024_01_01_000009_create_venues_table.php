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
        Schema::create('venues', function (Blueprint $table) {
            $table->id();
            $table->foreignId('owner_id')->constrained('users')->onDelete('restrict');
            $table->string('name', 150);
            $table->text('description')->nullable();
            $table->string('address', 255);
            $table->string('city', 100);
            $table->string('district', 100)->nullable();
            $table->decimal('latitude', 9, 6)->nullable();
            $table->decimal('longitude', 9, 6)->nullable();
            $table->string('phone', 30)->nullable();
            $table->time('open_time');
            $table->time('close_time');
            $table->boolean('is_active')->default(true);
            $table->timestamps();

            $table->index('owner_id');
            $table->index(['city', 'district']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('venues');
    }
};
