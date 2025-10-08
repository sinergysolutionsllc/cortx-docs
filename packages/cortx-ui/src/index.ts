// Components
export { Button, buttonVariants } from './components/button'
export type { ButtonProps } from './components/button'

export { Input } from './components/input'

export { Label } from './components/label'

export { Checkbox } from './components/checkbox'

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from './components/select'

// Charts
export { LineChart } from './components/charts/line-chart'
export type { LineChartProps } from './components/charts/line-chart'

export { BarChart } from './components/charts/bar-chart'
export type { BarChartProps } from './components/charts/bar-chart'

// Form Components
export { FormField } from './components/form/form-field'
export type { FormFieldProps } from './components/form/form-field'

export { FormError } from './components/form/form-error'
export type { FormErrorProps } from './components/form/form-error'

// ThinkTank AI Assistant
export {
  ThinkTankLogo,
  ThinkTankAssistant,
  ThinkTankPage
} from './components/thinktank'
export type {
  ThinkTankLogoProps,
  ThinkTankAssistantProps,
  ThinkTankPageProps,
  ThinkTankMessage,
  ThinkTankContext,
  RAGQueryRequest,
  RAGQueryResponse,
  RAGDocument,
  DocumentListResponse
} from './components/thinktank'

// Services
export { RAGService, createRAGService } from './services'
export type { RAGServiceConfig } from './services'

// Hooks
export { useThinkTankContext, useIsThinkTankPage } from './hooks'

// Utils
export { cn } from './utils/cn'

// Navigation System
export {
  CortexLink,
  SuiteSwitcher,
  GlobalNavigation,
  DomainNavigation,
} from './components/navigation'
export type {
  GlobalNavigationProps,
} from './components/navigation'

// Navigation Configuration
export {
  platformRoutes,
  fedSuiteRoutes,
  corpSuiteRoutes,
  medSuiteRoutes,
  allRoutes,
  suites,
  getRoutesByDomain,
  getRouteById,
  getRoutesByModule,
  isValidRoute,
} from './config/routes'
export type {
  Domain,
  SuiteModule,
  Route,
  SuiteInfo,
} from './config/routes'

// Navigation Types
export type {
  NavigationContext,
  NavigationProps,
  UserProfile,
  UserMenuProps,
  NavigationItem,
  SuiteSwitcherProps,
  DomainNavigationProps,
  LinkTarget,
  CortexLinkProps,
  SearchResult,
  GlobalSearchProps,
} from './types/navigation'

// Navigation Hooks (already exported from hooks/index.ts, but re-exporting for convenience)
export {
  useNavigationContext,
  useRouteBuilder,
  useActiveRoute,
  useIsActiveRoute,
  useDomainRoutes,
  detectDomain,
  buildUrl,
} from './hooks'
