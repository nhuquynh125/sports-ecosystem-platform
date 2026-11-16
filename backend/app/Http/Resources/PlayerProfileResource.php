<?php

namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;

class PlayerProfileResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id' => $this->id,
            'user_id' => $this->user_id,
            'sport_id' => $this->sport_id,
            'position' => $this->position,
            'skill_level' => $this->skill_level,
            'preferred_side' => $this->preferred_side,
            'height_cm' => $this->height_cm,
            'weight_kg' => $this->weight_kg !== null ? (float) $this->weight_kg : null,
            'city' => $this->city,
            'bio' => $this->bio,
            'is_visible' => (bool) $this->is_visible,
            'created_at' => $this->created_at?->toIso8601String(),
            'updated_at' => $this->updated_at?->toIso8601String(),
            'sport' => new SportResource($this->whenLoaded('sport')),
            'user' => $this->whenLoaded('user', function () {
                return [
                    'id' => $this->user->id,
                    'username' => $this->user->username,
                    'full_name' => $this->user->full_name,
                    'avatar_url' => $this->user->avatar_url,
                ];
            }),
        ];
    }
}
