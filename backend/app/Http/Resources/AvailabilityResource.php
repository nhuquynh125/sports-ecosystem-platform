<?php

namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;
use Carbon\Carbon;

class AvailabilityResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id' => $this->id,
            'player_profile_id' => $this->player_profile_id,
            'day_of_week' => $this->day_of_week,
            'start_time' => $this->start_time ? Carbon::parse($this->start_time)->format('H:i') : null,
            'end_time' => $this->end_time ? Carbon::parse($this->end_time)->format('H:i') : null,
            'created_at' => $this->created_at?->toIso8601String(),
        ];
    }
}
