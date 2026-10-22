<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Agent extends Model
{
    use HasUuids;

    public $incrementing = false;

    protected $keyType = 'string';

    protected $fillable = [
        'organization_id',
        'mode',
        'name',
        'description',
        'instructions',
        'engine',
        'provider',
        'temperature',
        'guardrails',
        'public_slug',
        'embed_allowed_origins',
        'conversations_count',
    ];

    protected function casts(): array
    {
        return [
            'embed_allowed_origins' => 'array',
            'guardrails' => 'boolean',
            'temperature' => 'float',
        ];
    }

    public function organization(): BelongsTo
    {
        return $this->belongsTo(Organization::class);
    }

    public function extension(): HasOne
    {
        return $this->hasOne(AgentExtension::class);
    }

    public function embedTokens(): HasMany
    {
        return $this->hasMany(EmbedToken::class);
    }

    public function knowledgeSources(): HasMany
    {
        return $this->hasMany(AgentKnowledgeSource::class);
    }

    public function isChatbot(): bool
    {
        return $this->mode === 'chatbot';
    }

    public function isAgent(): bool
    {
        return $this->mode === 'agent';
    }
}
