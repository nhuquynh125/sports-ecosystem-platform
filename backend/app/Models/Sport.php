<?php
namespace App\Models;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Sport extends Model {
    use HasFactory;
    protected $fillable = ['name', 'slug', 'icon_url', 'description', 'is_active'];
    protected $casts = ['is_active' => 'boolean'];
}
