import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { debounce } from 'lodash';
import { AssetFilters, Asset, User, Tenant } from '../types/api';
import { apiClient } from '../api/client';

export interface SearchState {
  // Search query and results
  query: string;
  assetResults: Asset[];
  userResults: User[];
  tenantResults: Tenant[];

  // Search metadata
  isSearching: boolean;
  hasSearched: boolean;
  totalResults: number;
  searchTime: number;

  // Recent searches and suggestions
  recentSearches: string[];
  searchSuggestions: string[];

  // Advanced filters
  assetFilters: AssetFilters;
  activeFilters: Record<string, any>;
  savedFilters: { name: string; filters: Record<string, any> }[];

  // Search history and analytics
  searchHistory: SearchHistoryItem[];

  // Actions
  setQuery: (query: string) => void;
  search: (query: string, filters?: Record<string, any>) => Promise<void>;
  searchAssets: (query: string, filters?: AssetFilters) => Promise<Asset[]>;
  clearSearch: () => void;
  clearResults: () => void;

  // Recent searches
  addRecentSearch: (query: string) => void;
  clearRecentSearches: () => void;
  removeRecentSearch: (query: string) => void;

  // Filters
  setActiveFilters: (filters: Record<string, any>) => void;
  clearActiveFilters: () => void;
  saveFilters: (name: string, filters: Record<string, any>) => void;
  applySavedFilters: (name: string) => void;
  removeSavedFilters: (name: string) => void;

  // Suggestions
  fetchSuggestions: (partial: string) => Promise<void>;
  clearSuggestions: () => void;

  // Search history
  addToHistory: (item: SearchHistoryItem) => void;
  clearHistory: () => void;
  getSearchAnalytics: () => SearchAnalytics;
}

interface SearchHistoryItem {
  id: string;
  query: string;
  filters: Record<string, any>;
  resultCount: number;
  timestamp: string;
  type: 'assets' | 'users' | 'tenants' | 'global';
}

interface SearchAnalytics {
  totalSearches: number;
  avgResultsPerSearch: number;
  mostSearchedTerms: { term: string; count: number }[];
  mostUsedFilters: { filter: string; count: number }[];
  searchTrends: { date: string; count: number }[];
}

const MAX_RECENT_SEARCHES = 10;
const MAX_SEARCH_HISTORY = 100;
const MAX_SUGGESTIONS = 5;

export const useSearchStore = create<SearchState>()(
  devtools(
    (set, get) => ({
      // Initial state
      query: '',
      assetResults: [],
      userResults: [],
      tenantResults: [],

      isSearching: false,
      hasSearched: false,
      totalResults: 0,
      searchTime: 0,

      recentSearches: JSON.parse(localStorage.getItem('recent_searches') || '[]'),
      searchSuggestions: [],

      assetFilters: {},
      activeFilters: {},
      savedFilters: JSON.parse(localStorage.getItem('saved_filters') || '[]'),

      searchHistory: JSON.parse(localStorage.getItem('search_history') || '[]'),

      // Set search query without triggering search
      setQuery: (query: string) => {
        set({ query });
      },

      // Perform global search across all entities
      search: async (query: string, filters = {}) => {
        if (!query.trim()) {
          get().clearResults();
          return;
        }

        set({ isSearching: true, query });
        const startTime = performance.now();

        try {
          // Search in parallel across different entity types
          const [assetResults, userResults, tenantResults] = await Promise.allSettled([
            // Search assets
            apiClient.get<{ data: Asset[] }>('/assets/', {
              params: {
                search: query,
                per_page: 20,
                ...filters,
              },
            }).then(response => response.data || []),

            // Search users (if user has permission)
            apiClient.get<{ data: User[] }>('/users/', {
              params: {
                search: query,
                per_page: 10,
              },
            }).then(response => response.data || []).catch(() => []),

            // Search tenants (if user has permission)
            apiClient.get<{ data: Tenant[] }>('/tenants/', {
              params: {
                search: query,
                per_page: 5,
              },
            }).then(response => response.data || []).catch(() => []),
          ]);

          const endTime = performance.now();
          const searchTime = endTime - startTime;

          const assets = assetResults.status === 'fulfilled' ? assetResults.value : [];
          const users = userResults.status === 'fulfilled' ? userResults.value : [];
          const tenants = tenantResults.status === 'fulfilled' ? tenantResults.value : [];

          const totalResults = assets.length + users.length + tenants.length;

          set({
            assetResults: assets,
            userResults: users,
            tenantResults: tenants,
            totalResults,
            searchTime,
            isSearching: false,
            hasSearched: true,
            activeFilters: filters,
          });

          // Add to search history
          get().addToHistory({
            id: `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            query,
            filters,
            resultCount: totalResults,
            timestamp: new Date().toISOString(),
            type: 'global',
          });

          // Add to recent searches
          get().addRecentSearch(query);

        } catch (error) {
          console.error('Search failed:', error);
          set({
            isSearching: false,
            hasSearched: true,
            assetResults: [],
            userResults: [],
            tenantResults: [],
            totalResults: 0,
          });
        }
      },

      // Search specifically for assets with advanced filtering
      searchAssets: async (query: string, filters = {}) => {
        const startTime = performance.now();

        try {
          const response = await apiClient.get<{ data: Asset[] }>('/assets/', {
            params: {
              search: query,
              per_page: 50,
              ...filters,
            },
          });

          const endTime = performance.now();
          const searchTime = endTime - startTime;

          const assets = response.data || [];

          set({
            assetResults: assets,
            searchTime,
            totalResults: assets.length,
            assetFilters: filters,
          });

          // Add to search history
          get().addToHistory({
            id: `asset-search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            query,
            filters,
            resultCount: assets.length,
            timestamp: new Date().toISOString(),
            type: 'assets',
          });

          return assets;

        } catch (error) {
          console.error('Asset search failed:', error);
          set({ assetResults: [] });
          return [];
        }
      },

      // Clear search query and results
      clearSearch: () => {
        set({
          query: '',
          assetResults: [],
          userResults: [],
          tenantResults: [],
          totalResults: 0,
          hasSearched: false,
          isSearching: false,
          searchTime: 0,
          activeFilters: {},
        });
      },

      // Clear only results, keep query
      clearResults: () => {
        set({
          assetResults: [],
          userResults: [],
          tenantResults: [],
          totalResults: 0,
          hasSearched: false,
          searchTime: 0,
        });
      },

      // Recent searches management
      addRecentSearch: (query: string) => {
        if (!query.trim()) return;

        const state = get();
        const normalizedQuery = query.trim().toLowerCase();

        // Remove duplicates and add to beginning
        const updatedSearches = [
          normalizedQuery,
          ...state.recentSearches.filter(search => search !== normalizedQuery),
        ].slice(0, MAX_RECENT_SEARCHES);

        set({ recentSearches: updatedSearches });
        localStorage.setItem('recent_searches', JSON.stringify(updatedSearches));
      },

      clearRecentSearches: () => {
        set({ recentSearches: [] });
        localStorage.removeItem('recent_searches');
      },

      removeRecentSearch: (query: string) => {
        const state = get();
        const updatedSearches = state.recentSearches.filter(search => search !== query);

        set({ recentSearches: updatedSearches });
        localStorage.setItem('recent_searches', JSON.stringify(updatedSearches));
      },

      // Filter management
      setActiveFilters: (filters: Record<string, any>) => {
        set({ activeFilters: filters });
      },

      clearActiveFilters: () => {
        set({ activeFilters: {} });
      },

      saveFilters: (name: string, filters: Record<string, any>) => {
        const state = get();
        const existingIndex = state.savedFilters.findIndex(sf => sf.name === name);

        let updatedFilters;
        if (existingIndex >= 0) {
          // Update existing
          updatedFilters = [...state.savedFilters];
          updatedFilters[existingIndex] = { name, filters };
        } else {
          // Add new
          updatedFilters = [...state.savedFilters, { name, filters }];
        }

        set({ savedFilters: updatedFilters });
        localStorage.setItem('saved_filters', JSON.stringify(updatedFilters));
      },

      applySavedFilters: (name: string) => {
        const state = get();
        const savedFilter = state.savedFilters.find(sf => sf.name === name);

        if (savedFilter) {
          set({ activeFilters: savedFilter.filters });
        }
      },

      removeSavedFilters: (name: string) => {
        const state = get();
        const updatedFilters = state.savedFilters.filter(sf => sf.name !== name);

        set({ savedFilters: updatedFilters });
        localStorage.setItem('saved_filters', JSON.stringify(updatedFilters));
      },

      // Search suggestions
      fetchSuggestions: async (partial: string) => {
        if (!partial.trim() || partial.length < 2) {
          set({ searchSuggestions: [] });
          return;
        }

        try {
          // Get suggestions from recent searches
          const state = get();
          const recentSuggestions = state.recentSearches
            .filter(search => search.toLowerCase().includes(partial.toLowerCase()))
            .slice(0, 3);

          // Get suggestions from asset names/tags (simplified approach)
          const assetSuggestions = state.assetResults
            .flatMap(asset => [asset.name, ...asset.tags])
            .filter(term => term.toLowerCase().includes(partial.toLowerCase()))
            .slice(0, 2);

          const allSuggestions = [...new Set([...recentSuggestions, ...assetSuggestions])]
            .slice(0, MAX_SUGGESTIONS);

          set({ searchSuggestions: allSuggestions });

        } catch (error) {
          console.error('Failed to fetch suggestions:', error);
          set({ searchSuggestions: [] });
        }
      },

      clearSuggestions: () => {
        set({ searchSuggestions: [] });
      },

      // Search history management
      addToHistory: (item: SearchHistoryItem) => {
        const state = get();
        const updatedHistory = [item, ...state.searchHistory]
          .slice(0, MAX_SEARCH_HISTORY);

        set({ searchHistory: updatedHistory });
        localStorage.setItem('search_history', JSON.stringify(updatedHistory));
      },

      clearHistory: () => {
        set({ searchHistory: [] });
        localStorage.removeItem('search_history');
      },

      // Search analytics
      getSearchAnalytics: (): SearchAnalytics => {
        const state = get();
        const history = state.searchHistory;

        if (history.length === 0) {
          return {
            totalSearches: 0,
            avgResultsPerSearch: 0,
            mostSearchedTerms: [],
            mostUsedFilters: [],
            searchTrends: [],
          };
        }

        // Calculate total searches
        const totalSearches = history.length;

        // Calculate average results per search
        const avgResultsPerSearch = history.reduce((sum, item) => sum + item.resultCount, 0) / totalSearches;

        // Find most searched terms
        const termCounts: Record<string, number> = {};
        history.forEach(item => {
          const term = item.query.toLowerCase();
          termCounts[term] = (termCounts[term] || 0) + 1;
        });

        const mostSearchedTerms = Object.entries(termCounts)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 10)
          .map(([term, count]) => ({ term, count }));

        // Find most used filters
        const filterCounts: Record<string, number> = {};
        history.forEach(item => {
          Object.keys(item.filters).forEach(filter => {
            filterCounts[filter] = (filterCounts[filter] || 0) + 1;
          });
        });

        const mostUsedFilters = Object.entries(filterCounts)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 10)
          .map(([filter, count]) => ({ filter, count }));

        // Calculate search trends (last 30 days)
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        const dailyCounts: Record<string, number> = {};
        history
          .filter(item => new Date(item.timestamp) >= thirtyDaysAgo)
          .forEach(item => {
            const date = item.timestamp.split('T')[0];
            dailyCounts[date] = (dailyCounts[date] || 0) + 1;
          });

        const searchTrends = Object.entries(dailyCounts)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([date, count]) => ({ date, count }));

        return {
          totalSearches,
          avgResultsPerSearch: Math.round(avgResultsPerSearch * 100) / 100,
          mostSearchedTerms,
          mostUsedFilters,
          searchTrends,
        };
      },
    }),
    {
      name: 'search-store',
      enabled: process.env.NODE_ENV === 'development',
    }
  )
);

// Create debounced search function
const debouncedSearch = debounce((searchFn: Function, query: string, filters?: any) => {
  searchFn(query, filters);
}, 300);

// Custom hook for debounced search
export const useDebouncedSearch = () => {
  const { search, searchAssets } = useSearchStore();

  const debouncedGlobalSearch = (query: string, filters?: Record<string, any>) => {
    debouncedSearch(search, query, filters);
  };

  const debouncedAssetSearch = (query: string, filters?: AssetFilters) => {
    debouncedSearch(searchAssets, query, filters);
  };

  return {
    debouncedGlobalSearch,
    debouncedAssetSearch,
  };
};

// Selectors for easy access
export const useSearch = () => {
  const store = useSearchStore();
  return {
    query: store.query,
    assetResults: store.assetResults,
    userResults: store.userResults,
    tenantResults: store.tenantResults,
    totalResults: store.totalResults,
    isSearching: store.isSearching,
    hasSearched: store.hasSearched,
    searchTime: store.searchTime,
  };
};

export const useSearchActions = () => {
  const store = useSearchStore();
  return {
    setQuery: store.setQuery,
    search: store.search,
    searchAssets: store.searchAssets,
    clearSearch: store.clearSearch,
    clearResults: store.clearResults,
  };
};

export const useSearchFilters = () => {
  const store = useSearchStore();
  return {
    activeFilters: store.activeFilters,
    savedFilters: store.savedFilters,
    setActiveFilters: store.setActiveFilters,
    clearActiveFilters: store.clearActiveFilters,
    saveFilters: store.saveFilters,
    applySavedFilters: store.applySavedFilters,
    removeSavedFilters: store.removeSavedFilters,
  };
};

export const useSearchSuggestions = () => {
  const store = useSearchStore();
  return {
    suggestions: store.searchSuggestions,
    recentSearches: store.recentSearches,
    fetchSuggestions: store.fetchSuggestions,
    clearSuggestions: store.clearSuggestions,
    addRecentSearch: store.addRecentSearch,
    clearRecentSearches: store.clearRecentSearches,
    removeRecentSearch: store.removeRecentSearch,
  };
};

export const useSearchAnalytics = () => {
  const store = useSearchStore();
  return {
    history: store.searchHistory,
    analytics: store.getSearchAnalytics(),
    clearHistory: store.clearHistory,
  };
};

export default useSearchStore;