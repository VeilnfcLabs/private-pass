using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace VeilPass;

/// <summary>
/// Wrapper client for the VeilPass API.
/// </summary>
public class VeilPassClient
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;

    public VeilPassClient(string baseUrl = "http://localhost:8000", string? apiKey = null)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _http = new HttpClient();
        _http.DefaultRequestHeaders.Add("Content-Type", "application/json");
        _http.Timeout = TimeSpan.FromSeconds(30);

        if (!string.IsNullOrEmpty(apiKey))
            _http.DefaultRequestHeaders.Add("X-API-Key", apiKey);
    }

    private async Task<JsonDocument> PostAsync(string path, object body)
    {
        var json = JsonSerializer.Serialize(body, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        });

        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _http.PostAsync(_baseUrl + path, content);
        var responseBody = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
        {
            throw new HttpRequestException(
                $"API error (HTTP {(int)response.StatusCode}): {responseBody}");
        }

        return JsonDocument.Parse(responseBody);
    }

    private static void Log(string label, JsonDocument doc)
    {
        Console.WriteLine($"\n── {label} ──");
        Console.WriteLine(JsonSerializer.Serialize(doc, new JsonSerializerOptions { WriteIndented = true }));
    }
}
