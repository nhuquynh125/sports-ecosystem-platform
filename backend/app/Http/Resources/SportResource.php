<?php

namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;

class SportResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'slug' => $this->slug,
            'description' => $this->description,
            'icon_url' => $this->icon_url,
            'is_active' => (bool) $this->is_active,
        ];
    }
}
