<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class EmbedToken extends Model
{
    protected $fillable = ['agent_id', 'token', 'allowed_origins', 'is_active'];

    protected function casts(): array
    {
        return [
            'allowed_origins' => 'array',
            'is_active' => 'boolean',
        ];
    }

    public function agent(): BelongsTo
    {
        return $this->belongsTo(Agent::class);
    }
}
