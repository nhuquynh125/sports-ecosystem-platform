<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class CourtResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'venue_id' => $this->venue_id,
            'sport_id' => $this->sport_id,
            'sport' => $this->whenLoaded('sport', function () {
                return [
                    'id' => $this->sport->id,
                    'name' => $this->sport->name,
                    'slug' => $this->sport->slug,
                    'description' => $this->sport->description ?? null,
                    'icon_url' => $this->sport->icon_url ?? null,
                    'is_active' => (bool) $this->sport->is_active,
                ];
            }, $this->sport ? [
                'id' => $this->sport->id,
                'name' => $this->sport->name,
                'slug' => $this->sport->slug,
                'description' => $this->sport->description ?? null,
                'icon_url' => $this->sport->icon_url ?? null,
                'is_active' => (bool) $this->sport->is_active,
            ] : null),
            'name' => $this->name,
            'surface_type' => $this->surface_type,
            'capacity' => $this->capacity !== null ? (int) $this->capacity : null,
            'hourly_price' => (float) $this->hourly_price,
            'is_active' => (bool) $this->is_active,
            'created_at' => $this->created_at ? $this->created_at->toIso8601String() : null,
            'updated_at' => $this->updated_at ? $this->updated_at->toIso8601String() : null,
        ];
    }
}
