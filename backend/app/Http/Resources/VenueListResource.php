<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class VenueListResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        $activeCourts = $this->courts ? $this->courts->where('is_active', true) : collect();
        $sports = $activeCourts->map(function ($court) {
            return $court->sport ? [
                'id' => $court->sport->id,
                'name' => $court->sport->name,
                'slug' => $court->sport->slug,
            ] : null;
        })->filter()->unique('id')->values()->toArray();

        return [
            'id' => $this->id,
            'owner_id' => $this->owner_id,
            'name' => $this->name,
            'description' => $this->description,
            'address' => $this->address,
            'city' => $this->city,
            'district' => $this->district,
            'latitude' => $this->latitude !== null ? (float) $this->latitude : null,
            'longitude' => $this->longitude !== null ? (float) $this->longitude : null,
            'phone' => $this->phone,
            'open_time' => $this->open_time,
            'close_time' => $this->close_time,
            'is_active' => (bool) $this->is_active,
            'created_at' => $this->created_at ? $this->created_at->toIso8601String() : null,
            'updated_at' => $this->updated_at ? $this->updated_at->toIso8601String() : null,
            'court_count' => $activeCourts->count(),
            'min_hourly_price' => $activeCourts->min('hourly_price') !== null ? (float) $activeCourts->min('hourly_price') : null,
            'sports' => $sports,
        ];
    }
}
