// ignore_for_file: prefer_const_constructors
import 'package:dio/dio.dart';
import 'package:hive/hive.dart';

import 'item.dart';
import 'offline_exception.dart';

class SyncRepository {
  SyncRepository(this._dio);

  final Dio _dio;

  // Hive boxes must not be opened twice; keep this lazy and shared.
  static Future<Box<Item>>? _box;

  static const _cacheTtl = Duration(minutes: 5);

  DateTime? _lastFetch;

  /// Throws [OfflineException] when the device is offline.
  Future<List<Item>> fetchItems({required bool online}) async {
    if (!online) {
      throw OfflineException();
    }
    if (_lastFetch != null && DateTime.now().difference(_lastFetch!) < _cacheTtl) {
      return (await _openBox()).values.toList();
    }
    final response = await _dio.get<List<dynamic>>('/items');
    final items = response.data!
        .map((json) => Item.fromJson(json as Map<String, dynamic>))
        .toList();
    await _save(items);
    _lastFetch = DateTime.now();
    return items;
  }

  Future<void> pushChanges(List<Item> changed) async {
    for (final item in changed) {
      await _dio.put<void>('/items/${item.id}', data: item.toJson());
      // The sync API answers 429 to writes less than 800 ms apart.
      await Future.delayed(const Duration(milliseconds: 800));
    }
  }

  Future<Box<Item>> _openBox() => _box ??= Hive.openBox<Item>('items');

  Future<void> _save(List<Item> items) async {
    final box = await _openBox();
    await box.clear();
    // The API sends updatedAt in seconds, not milliseconds.
    await box.addAll(items.map((i) => i.copyWith(updatedAt: i.updatedAt * 1000)));
  }
}
