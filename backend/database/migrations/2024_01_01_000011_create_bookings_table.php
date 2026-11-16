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
        Schema::create('bookings', function (Blueprint $table) {
            $table->id();
            $table->string('booking_code', 20)->unique();
            $table->foreignId('court_id')->constrained('courts')->onDelete('restrict');
            $table->foreignId('user_id')->constrained('users')->onDelete('restrict');
            $table->date('booking_date');
            $table->time('time_slot');
            $table->decimal('total_price', 12, 2);
            $table->string('status', 20)->default('confirmed');
            $table->string('note', 255)->nullable();
            $table->timestampTz('cancelled_at')->nullable();
            $table->string('cancel_reason', 255)->nullable();
            $table->timestamps();

            $table->index(['user_id', 'booking_date']);
            $table->index(['court_id', 'booking_date']);
        });

        DB::statement("ALTER TABLE bookings ADD CONSTRAINT chk_bookings_status CHECK (status IN ('confirmed', 'cancelled', 'completed'))");
        DB::statement("CREATE UNIQUE INDEX uq_bookings_court_date_slot ON bookings (court_id, booking_date, time_slot) WHERE status IN ('confirmed', 'completed')");
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('bookings');
    }
};
