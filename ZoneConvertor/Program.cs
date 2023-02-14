// Copyright (c) 2020 ALT LLC
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of source code located below and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//  
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//  
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading;
using System.Xml.Linq;

public struct ZoneDescription {
    public ZoneDescription() {
    }
    public float Width { get; set; } = 0.0f;
    public float Height { get; set; } = 0.0f;
    public float CellSize { get; set; } = 0.0f;

    public List<Antilatency.Math.float3> Markers { get; set; } = new List<Antilatency.Math.float3>();
}

class Program {

    static int Main(string[] args) {
        if (args.Count() < 1) {
            Console.WriteLine($"Specify tracking zone url in argv[1]");
            return -1;
        }

        var link = args[0];
        string environmentCode = link;

        string prefix = "?data=";
        string suffix = "&name";

        if (link.Contains(prefix)) {
             environmentCode = link.Substring(link.IndexOf(prefix) + prefix.Length);
            if(link.Contains(suffix)) {
                environmentCode = environmentCode.Remove(environmentCode.IndexOf(suffix));
            }
        }
        Console.WriteLine($"Used environmentCode: {environmentCode}");
        using var environmentSelectorLibrary = Antilatency.Alt.Environment.Selector.Library.load();

        using var environment = environmentSelectorLibrary.createEnvironment(environmentCode);

        var markers = environment.getMarkers();

        var zoneDesciption = new ZoneDescription();

        for (var i = 0; i < markers.Length; ++i) {
            zoneDesciption.Markers.Add(markers[i]);
        }

        Console.WriteLine($"Fill {zoneDesciption.Markers.Count} markers");

        var resultFilename = "ZoneDescription.json";

        var result = JObject.FromObject(zoneDesciption);

        File.WriteAllText(resultFilename, result.ToString());

        Console.WriteLine($"Info saved to {Path.GetFullPath(resultFilename)}");
        return 0;
    }
}
