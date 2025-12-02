"use client";

import { useState } from "react";
import { Search, Globe, Languages, Loader2, CheckCircle, AlertCircle, Info } from "lucide-react";
import { Card, CardHeader, CardBody, Button, Input, Select } from "@/components/ui";
import { Header, PageContent } from "@/components/layout";
import { searchByKeyword } from "@/lib/api";

// Country options
const COUNTRIES = [
  { value: "FR", label: "France" },
  { value: "US", label: "United States" },
  { value: "DE", label: "Germany" },
  { value: "GB", label: "United Kingdom" },
  { value: "ES", label: "Spain" },
  { value: "IT", label: "Italy" },
  { value: "BE", label: "Belgium" },
  { value: "NL", label: "Netherlands" },
  { value: "CH", label: "Switzerland" },
  { value: "CA", label: "Canada" },
  { value: "AU", label: "Australia" },
];

// Language options
const LANGUAGES = [
  { value: "", label: "Toutes les langues" },
  { value: "fr", label: "Francais" },
  { value: "en", label: "English" },
  { value: "de", label: "Deutsch" },
  { value: "es", label: "Espanol" },
  { value: "it", label: "Italiano" },
  { value: "nl", label: "Nederlands" },
];

interface SearchResult {
  scan_id: string;
  keyword: string;
  country: string;
  ads_found: number;
  pages_found: number;
  new_pages: number;
}

/**
 * Search Page
 *
 * Allows users to search for ads via the Meta Ads Library API.
 */
export default function SearchPage() {
  const [keywords, setKeywords] = useState("");
  const [country, setCountry] = useState("FR");
  const [language, setLanguage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentKeyword, setCurrentKeyword] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!keywords.trim()) {
      setError("Veuillez entrer au moins un mot-cle");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults([]);

    // Split keywords by semicolon and trim
    const keywordList = keywords
      .split(";")
      .map((k) => k.trim())
      .filter((k) => k.length > 0);

    if (keywordList.length === 0) {
      setError("Veuillez entrer au moins un mot-cle valide");
      setIsLoading(false);
      return;
    }

    try {
      // Process each keyword sequentially
      for (const keyword of keywordList) {
        setCurrentKeyword(keyword);

        const result = await searchByKeyword({
          keyword,
          country,
          language: language || undefined,
          limit: 50,
        });

        setResults((prev) => [...prev, result]);
      }

      setCurrentKeyword(null);
    } catch (err) {
      console.error("Search error:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Une erreur est survenue lors de la recherche"
      );
    } finally {
      setIsLoading(false);
      setCurrentKeyword(null);
    }
  };

  const totalAdsFound = results.reduce((sum, r) => sum + r.ads_found, 0);
  const totalPagesFound = results.reduce((sum, r) => sum + r.pages_found, 0);
  const totalNewPages = results.reduce((sum, r) => sum + r.new_pages, 0);

  return (
    <>
      <Header
        title="Recherche"
        subtitle="Recherchez des annonces actives via l'API Meta Ads Library"
      />
      <PageContent>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Search className="w-5 h-5 text-blue-400" />
                  Nouvelle recherche
                </div>
              </CardHeader>
              <CardBody className="space-y-6">
                {/* Keywords Input */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Mots-cles <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    placeholder="Entrez vos mots-cles separes par des points-virgules&#10;Exemple: dropshipping; ecommerce; AliExpress"
                    className="w-full h-24 px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    disabled={isLoading}
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Separez les mots-cles par des points-virgules (;)
                  </p>
                </div>

                {/* Country Select */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Globe className="w-4 h-4 inline mr-1" />
                    Pays <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                  >
                    {COUNTRIES.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Language Select */}
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    <Languages className="w-4 h-4 inline mr-1" />
                    Langue (optionnel)
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l.value} value={l.value}>
                        {l.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                  </div>
                )}

                {/* Search Button */}
                <Button
                  onClick={handleSearch}
                  disabled={isLoading || !keywords.trim()}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Recherche en cours...
                      {currentKeyword && (
                        <span className="ml-2 text-slate-400">
                          ({currentKeyword})
                        </span>
                      )}
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Lancer la recherche
                    </>
                  )}
                </Button>
              </CardBody>
            </Card>

            {/* Results */}
            {results.length > 0 && (
              <Card className="mt-6">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    Resultats de la recherche
                  </div>
                </CardHeader>
                <CardBody>
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-slate-800 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-slate-200">
                        {totalAdsFound}
                      </p>
                      <p className="text-sm text-slate-400">Annonces trouvees</p>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-slate-200">
                        {totalPagesFound}
                      </p>
                      <p className="text-sm text-slate-400">Pages trouvees</p>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-400">
                        {totalNewPages}
                      </p>
                      <p className="text-sm text-slate-400">Nouvelles pages</p>
                    </div>
                  </div>

                  {/* Details per keyword */}
                  <div className="space-y-3">
                    {results.map((result, index) => (
                      <div
                        key={result.scan_id || index}
                        className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-slate-200">
                            {result.keyword}
                          </p>
                          <p className="text-sm text-slate-500">
                            {result.country}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-300">
                            {result.ads_found} annonces, {result.pages_found} pages
                          </p>
                          {result.new_pages > 0 && (
                            <p className="text-sm text-green-400">
                              +{result.new_pages} nouvelles
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            )}
          </div>

          {/* Help Card */}
          <div>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Info className="w-5 h-5 text-blue-400" />
                  Comment utiliser
                </div>
              </CardHeader>
              <CardBody>
                <ul className="space-y-3 text-sm text-slate-400">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">1.</span>
                    <span>
                      Entrez vos mots-cles separes par des points-virgules
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">2.</span>
                    <span>Choisissez le pays cible (obligatoire)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">3.</span>
                    <span>Selectionnez une langue (optionnel)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5">4.</span>
                    <span>
                      Cliquez sur "Lancer la recherche" pour demarrer l'analyse
                    </span>
                  </li>
                </ul>

                <div className="mt-6 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <p className="text-sm text-blue-400">
                    Les pages trouvees seront automatiquement ajoutees a la base
                    de donnees et visibles dans l'onglet "Pages / Shops".
                  </p>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </PageContent>
    </>
  );
}
