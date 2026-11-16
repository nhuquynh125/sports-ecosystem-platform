<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration {
    public function up(): void {
        Schema::create('venues', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('owner_id');
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
            $table->foreign('owner_id')->references('id')->on('users')->onDelete('restrict');
        });
        DB::statement("CREATE INDEX ix_venues_owner_id ON venues (owner_id)");
        DB::statement("CREATE INDEX ix_venues_city_district ON venues (city, district)");

        Schema::create('courts', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('venue_id');
            $table->unsignedSmallInteger('sport_id');
            $table->string('name', 100);
            $table->string('surface_type', 20)->nullable();
            $table->boolean('has_lighting')->default(false);
            $table->decimal('price_per_slot', 10, 2)->nullable();
            $table->integer('slot_duration_minutes')->default(60);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
            $table->foreign('venue_id')->references('id')->on('venues')->onDelete('cascade');
            $table->foreign('sport_id')->references('id')->on('sports')->onDelete('restrict');
        });

        Schema::create('bookings', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('court_id');
            $table->unsignedBigInteger('user_id');
            $table->date('booking_date');
            $table->time('time_slot');
            $table->integer('duration_slots')->default(1);
            $table->string('status', 20)->default('confirmed');
            $table->decimal('total_price', 10, 2)->nullable();
            $table->text('notes')->nullable();
            $table->timestamps();
            $table->foreign('court_id')->references('id')->on('courts')->onDelete('restrict');
            $table->foreign('user_id')->references('id')->on('users')->onDelete('restrict');
        });
        // Double-booking guard: unique index on (court_id, booking_date, time_slot) for active bookings
        DB::statement("CREATE UNIQUE INDEX uq_bookings_court_date_slot ON bookings (court_id, booking_date, time_slot) WHERE status IN ('confirmed','completed')");
        DB::statement("ALTER TABLE bookings ADD CONSTRAINT ck_bookings_status CHECK (status IN ('confirmed','cancelled','completed','pending'))");
        DB::statement("CREATE INDEX ix_bookings_court_id ON bookings (court_id)");
        DB::statement("CREATE INDEX ix_bookings_user_id ON bookings (user_id)");
        DB::statement("CREATE INDEX ix_bookings_booking_date ON bookings (booking_date)");
    }

    public function down(): void {
        Schema::dropIfExists('bookings');
        Schema::dropIfExists('courts');
        Schema::dropIfExists('venues');
    }
};
