export interface MCardConfig {
    apiKey?: string;
    baseUrl?: string;
}

export interface MCard {
    content: string | Buffer;
    hash: string;
    g_time: string;
}

export interface CreateCardParams {
    content: string | Buffer;
}

export interface HealthStatus {
    status: 'healthy' | 'unhealthy';
}
