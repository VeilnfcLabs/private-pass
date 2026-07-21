using System;
using System.Text.Json;
using System.Threading.Tasks;

namespace VeilPass;

/// <summary>
/// VeilPass API — C# example
///
/// Demonstrates all 6 API operations using the VeilPassClient wrapper.
/// Run: dotnet run
/// </summary>
class Program
{
    static async Task Main(string[] args)
    {
        var apiBase = Environment.GetEnvironmentVariable("VEILPASS_API_URL") ?? "http://localhost:8000";
        var apiKey = Environment.GetEnvironmentVariable("VEILPASS_API_KEY") ?? "";

        var client = new VeilPassClient(apiBase, apiKey);

        await client.GenerateQRAsync();
        await client.GenerateNFCAsync();
        await client.CreateSignedLinkAsync();
        await client.CreateSignedURLAsync();
        var token = await client.GenerateTokenAsync();

        var tokenStr = token.RootElement.GetProperty("token").GetString()!;
        await client.VerifyAsync("token", tokenStr);

        Console.WriteLine("\n✅ All API operations completed successfully.");
    }
}
