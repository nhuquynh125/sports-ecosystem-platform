<?php

namespace App\Http\Resources;

use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class BookingResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        $court = $this->court;
        $venue = $court ? $court->venue : null;

        $endTime = $this->time_slot;
        if ($this->time_slot) {
            try {
                $endTime = Carbon::createFromFormat('H:i:s', strlen($this->time_slot) === 5 ? $this->time_slot . ':00' : $this->time_slot)
                    ->addHour()
                    ->format('H:i:s');
            } catch (\Exception $e) {
                $endTime = null;
            }
        }

        $bookingDateStr = $this->booking_date instanceof \DateTimeInterface
            ? $this->booking_date->format('Y-m-d')
            : (string) $this->booking_date;

        return [
            'id' => $this->id,
            'booking_code' => $this->booking_code,
            'court_id' => $this->court_id,
            'court' => $court ? new CourtResource($court) : null,
            'user_id' => $this->user_id,
            'booking_date' => $bookingDateStr,
            'time_slot' => $this->time_slot,
            'end_time' => $endTime,
            'total_price' => (float) $this->total_price,
            'status' => $this->status,
            'note' => $this->note,
            'cancelled_at' => $this->cancelled_at ? $this->cancelled_at->toIso8601String() : null,
            'cancel_reason' => $this->cancel_reason,
            'created_at' => $this->created_at ? $this->created_at->toIso8601String() : null,
            'updated_at' => $this->updated_at ? $this->updated_at->toIso8601String() : null,
            'venue_id' => $court ? (int) $court->venue_id : 0,
            'venue_name' => $venue ? $venue->name : '',
            'court_name' => $court ? $court->name : '',
        ];
    }
}
