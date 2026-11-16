<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\SportResource;
use App\Models\Sport;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class SportController extends Controller
{
    public function index(): JsonResponse
    {
        $sports = Sport::where('is_active', true)->orderBy('name')->get();
        return response()->json(SportResource::collection($sports));
    }

    public function show(int $id): JsonResponse
    {
        $sport = Sport::findOrFail($id);
        return response()->json(new SportResource($sport));
    }

    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'required|string|max:60|unique:sports,name',
            'slug' => 'nullable|string|max:70|unique:sports,slug',
            'description' => 'nullable|string',
            'icon_url' => 'nullable|string|max:500',
            'is_active' => 'nullable|boolean',
        ]);

        if (empty($validated['slug'])) {
            $validated['slug'] = Str::slug($validated['name']);
        }

        $sport = Sport::create($validated);
        return response()->json(new SportResource($sport), 201);
    }

    public function update(Request $request, int $id): JsonResponse
    {
        $sport = Sport::findOrFail($id);

        $validated = $request->validate([
            'name' => 'nullable|string|max:60|unique:sports,name,' . $sport->id,
            'slug' => 'nullable|string|max:70|unique:sports,slug,' . $sport->id,
            'description' => 'nullable|string',
            'icon_url' => 'nullable|string|max:500',
            'is_active' => 'nullable|boolean',
        ]);

        $sport->update(array_filter($validated, fn($val) => $val !== null));
        return response()->json(new SportResource($sport));
    }
}
