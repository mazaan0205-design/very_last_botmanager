<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class AgentExtension extends Model
{
    public $incrementing = false;

    protected $primaryKey = 'agent_id';

    protected $keyType = 'string';

    protected $fillable = ['agent_id', 'enabled_tools'];

    protected function casts(): array
    {
        return ['enabled_tools' => 'array'];
    }

    public function agent(): BelongsTo
    {
        return $this->belongsTo(Agent::class);
    }
}
