import 'package:flutter/foundation.dart';

import 'cancel_token.dart';
import 'item_repository.dart';

sealed class ItemsState {}

class ItemsLoading extends ItemsState {}

class ItemsEmpty extends ItemsState {}

class ItemsError extends ItemsState {
  ItemsError(this.message);
  final String message;
}

class ItemsLoaded extends ItemsState {
  ItemsLoaded(this.items);
  final List<Item> items;
}

class ItemsController extends ChangeNotifier {
  ItemsController(this._repository);

  final ItemRepository _repository;
  ItemsState _state = ItemsLoading();
  CancelToken? _token;
  bool _disposed = false;

  ItemsState get state => _state;

  Future<void> load({bool showLoader = true}) async {
    _token?.cancel();
    final token = _token = CancelToken();
    if (showLoader) _emit(ItemsLoading());
    try {
      final items = await _repository.fetchItems(token);
      if (token.isCancelled) return;
      _emit(items.isEmpty ? ItemsEmpty() : ItemsLoaded(items));
    } on CancelledException {
      return;
    } catch (_) {
      if (token.isCancelled) return;
      _emit(ItemsError('Не удалось загрузить данные'));
    }
  }

  void _emit(ItemsState state) {
    if (_disposed) return;
    _state = state;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _token?.cancel();
    super.dispose();
  }
}
